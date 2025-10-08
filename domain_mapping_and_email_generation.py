import pandas as pd
import json
import time
import re
import math
from difflib import SequenceMatcher
import os
from vertexai.generative_models import GenerativeModel

# Set up environment variable for Google Vertex AI
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "admazes-elk-gcp-demo-d11fd228fd9a.json"

# Initialize AI model
model = GenerativeModel("gemini-1.5-pro")

def preprocess_name(name):
    """Clean the company name by removing special characters and common keywords."""
    if not isinstance(name, str):
        return ''
    # Convert to lowercase, remove non-alphanumeric, non-Chinese, and non-Japanese characters, and delete specific keywords
    clean_name = re.sub(r'[^\w\u4e00-\u9fff\u3040-\u30ff\u31f0-\u31ff]', '', name.lower())
    clean_name = re.sub(r'(股份有限公司|有限公司|公司|company|inc|pvt)', '', clean_name)
    clean_name = clean_name.strip()
    return clean_name

def clean_domain(domain):
    """Remove protocols, www, and common domain-related keywords."""
    # Use regular expressions to remove specific content
    domain = re.sub(r'https?://(www\.)?', '', domain)  # Remove http(s) and www.
    domain = re.sub(r'(org|com|hk|team|group|company|inc|pvt|limited|ltd)', '', domain)  # Remove specific keywords
    domain = re.sub(r'[^a-zA-Z0-9]', '', domain)  # Remove all non-alphanumeric characters
    return domain

def calculate_similarity(a, b):
    """Calculate the similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def load_data():
    """Load participant data and customer list."""
    with open('participant_data.json', 'r') as file:
        participant_data = json.load(file)
    customer_list = pd.read_csv("Google Cloud Summit 2024 Customer List - Summit.csv")
    return participant_data, customer_list

def filter_participants(participant_data):
    """Filter participants by removing invalid entries and cleaning their company names."""
    return [
        {
            'name': p['name'],  
            'company': p['company'],  
            'company_clean': preprocess_name(p['company'])  
        }
        for p in participant_data
        if not (
            # Exclude entries where 'name' or 'company' is NaN
            (isinstance(p.get('name'), float) and math.isnan(p.get('name'))) or
            (isinstance(p.get('company'), float) and math.isnan(p.get('company'))) or
            
            # Exclude entries where 'name' is in the list of invalid values
            p.get('name') in ['N/A', '-', '/', 'NA'] or
            
            # Exclude entries where 'company' is in the list of invalid values
            p.get('company') in ['N/A', '-', '/', 'NA', 'HK', 'Hong Kong', 'China'] or
            
            # Exclude entries where the length of 'company' is 2 or less
            len(p.get('company', '')) <= 2
        )
    ]


def prepare_customer_data(customer_list):
    """Clean and process customer data for domain mapping."""
    df = customer_list[['Company', 'Domain']]
    df['Company_English_Name'] = df['Domain'].apply(clean_domain)
    df['Company'] = df['Company'].apply(preprocess_name)
    return df.drop_duplicates()

def add_domain(participant, df_company_domain_clean):
    """Find possible domains for each participant based on company name similarity."""
    processed_company = participant['company_clean']
    matched_domains = []

    for _, row in df_company_domain_clean.iterrows():
        company_clean = row["Company"]
        company_english_clean = row["Company_English_Name"]

        # If the company name has 4 or fewer characters, only check for exact matches
        if len(processed_company) <= 4:
            if (processed_company in company_clean or processed_company in company_english_clean) and \
                    processed_company in row["Domain"]:
                matched_domains.append(row["Domain"])
        else:
            # Check for exact matches in company_clean or company_english_clean
            if processed_company in company_clean or processed_company in company_english_clean:
                matched_domains.append(row["Domain"])

            # Check for similarity greater than 0.8
            if any(calculate_similarity(processed_company, name) > 0.8 
                   for name in [company_clean, company_english_clean]):
                matched_domains.append(row["Domain"])

    # Assign unique matched domains to the participant
    participant['possible_domain'] = list(set(matched_domains))
    return participant

def generate_prompt(participant, customer_dict_list):
    prompt = f"""
    You are excellent at guessing people's email addresses. 
    Now, I will provide you with some information about an individual, including their name, company name, and a list of possible company domains. 
    
    For each domain in the provided list, refer to the email naming conventions used by other employees of the same company, and generate at least ten possible email addresses following the observed pattern for that domain.
    Here are some examples of other people from the same company:
    {[customer for customer in customer_dict_list if customer.get('Domain') in participant['possible_domain']]}
    
    New input: 
    {participant}          

    Your output should be a valid JSON string with double quotes, in the following format:
    Combine all the possible email addresses from all domains into a single list.
    {{"possible_email": ["email1@domain1.com", "email2@domain1.com", ..., "email1@domain2.com", "email2@domain2.com", ...]}}

    """
    return prompt

def generate_possible_emails(participant, model, customer_dict_list):
    """Use AI model to generate possible emails based on the provided data."""
    retries, attempt, success = 3, 0, False
    while attempt < retries and not success:
        try:
            response = model.generate_content(generate_prompt(participant, customer_dict_list)).text
            cleaned_response = response.replace('```json', '').replace('```', '').replace('\\n', '').replace('\n', '').strip()
            participant['possible_email'] = json.loads(cleaned_response)['possible_email']
            success = True
        except Exception as e:
            print(f"Error for {participant['name']} (Attempt {attempt + 1}): {str(e)}")
            attempt += 1
            time.sleep(2)
    if not success:
        participant['possible_email'] = []
    return participant

def main():
    """Main function to execute the workflow."""
    participant_data, customer_list = load_data()
    filtered_participants = filter_participants(participant_data)
    df_company_domain_clean = prepare_customer_data(customer_list)
    customer_dict_list = customer_list[['First Name', 'Last Name', 'Email', 'Domain']].to_dict(orient='records')
    
    # Map domains to participants
    participant_domain_data = [add_domain(p, df_company_domain_clean) for p in filtered_participants]
    
    # Filter participants with at least one possible domain
    filtered_data_participant = [p for p in participant_domain_data if p['possible_domain']]
    
    # Generate possible emails
    for participant in filtered_data_participant:
        generate_possible_emails(participant, model, customer_dict_list)
        print(f"{participant['name']} - Emails generated")
    
    # Save the results to a JSON file
    output_file = "filtered_participant_data_with_emails.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_data_participant, f, indent=5, ensure_ascii=False)
    print(f"Filtered data saved to {output_file}")

# Execute the main function
if __name__ == "__main__":
    main()
