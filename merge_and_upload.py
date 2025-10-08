import json
import smtplib
import random
import string
import dns.resolver
import time
from pymongo import MongoClient

# === Configuration ===
RESULTS_FILE = "participant_data_with_valid_email.json"

# === Data Processing Functions ===

def load_json(input_file):
    """Load JSON data from file."""
    with open(input_file, 'r', encoding="utf-8") as file:
        return json.load(file)

def save_json(data, output_file):
    """Save data to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=7, ensure_ascii=False)

def filter_valid_participants(participant_data_email):
    """
    Clean and filter participants that have non-empty valid_email fields.
    Removes duplicate emails from each participant's valid_email list.
    """
    for participant in participant_data_email:
        # Remove duplicates from valid_email
        if 'valid_email' in participant:
            participant['valid_email'] = list(set(participant['valid_email']))
        
    return [participant for participant in participant_data_email if participant.get('valid_email')] 

def extract_valid_email_info(valid_participants):
    """Extract name, company, and valid_email fields from valid participants."""
    return [
        {k: v for k, v in participant.items() if k in {'name', 'company', 'valid_email'}}
        for participant in valid_participants
    ]

def create_valid_email_dict(valid_email):
    """Create a dictionary keyed by (name, company) with valid_email as the value."""
    return {
        (entry["name"], entry["company"]): entry["valid_email"]
        for entry in valid_email
    }

def merge_valid_email(participant_data, valid_email_dict):
    """Merge valid email data into the original participant records."""
    for participant in participant_data:
        key = (participant["name"], participant["company"])
        if key in valid_email_dict:
            participant["valid_email"] = valid_email_dict[key]
        else:
            participant["valid_email"] = []

# === Catch-All Detection Functions ===

def get_email_domain(email):
    """Extract the domain from an email address."""
    return email.split('@')[-1]

def generate_random_email(domain):
    """Generate a random email address for a given domain."""
    local_part = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"{local_part}@{domain}"

def get_mx_host(domain):
    """Get the MX record (mail server) for a given domain."""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return mx_records[0].exchange.to_text().strip()
    except:
        return None

def is_catch_all_domain(domain):
    """
    Determine if a domain is catch-all.
    If sending to a random address still returns 250, it's likely a catch-all domain.
    """
    mx_host = get_mx_host(domain)
    if not mx_host:
        return False

    test_email = generate_random_email(domain)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with smtplib.SMTP(mx_host, 25, timeout=10) as server:
                server.helo()
                server.mail("test@example.com")
                code, _ = server.rcpt(test_email)
                return code == 250
        except Exception as e:
            print(f"Attempt {attempt}: SMTP error on {domain}: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                return False
    return False

def get_catch_all_domain_set(valid_participants):
    """Return a set of domains that are identified as catch-all."""
    print("Checking for catch-all domains...")
    domains = {
        get_email_domain(email)
        for participant in valid_participants
        for email in participant['valid_email']
    }

    catch_all_domains = {
        domain for domain in domains if is_catch_all_domain(domain)
    }

    if catch_all_domains:
        print(f"Detected catch-all domains: {catch_all_domains}")
    else:
        print("No catch-all domains detected.")

    return catch_all_domains

# === MongoDB Functions ===

def connect_to_mongodb():
    """Connect to MongoDB and return the target collection."""
    conn = MongoClient("mongodb://mila:Admazetest123@mongodb-prd.admazes.marketing:27017/dev_db_mila")
    db = conn.dev_db_mila
    return db.participant_info

def delete_existing_collection(collection):
    """Delete the existing MongoDB collection."""
    collection.drop()
    print("Existing MongoDB collection deleted.")

def upload_to_mongodb(collection, json_file):
    """Upload the updated participant data to MongoDB."""
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    if isinstance(data, list):
        collection.insert_many(data)
    else:
        collection.insert_one(data)

    print("New data uploaded to MongoDB.")

# === Add Catch-All Flags ===

def add_catch_all_flag(participant_data, catch_all_domains):
    """Add 'catch-all' flag to each participant entry."""
    for entry in participant_data:
        domain_list = [get_email_domain(email) for email in entry.get("valid_email", [])]
        is_catch_all = any(domain in catch_all_domains for domain in domain_list)
        entry["catch-all"] = "True" if is_catch_all else "False"
    return participant_data

# === Main Processing Pipeline ===

def process_data(participant_data_json, participant_data_email_json):
    """Process participant data with valid email filtering and MongoDB upload."""
    print("Loading data...")
    participant_data = load_json(participant_data_json)
    participant_data_email = load_json(participant_data_email_json)

    # Filter participants with at least one valid email
    valid_participants = filter_valid_participants(participant_data_email)

    # Get catch-all domains
    catch_all_domains = get_catch_all_domain_set(valid_participants)

    # Extract and merge email info
    valid_email = extract_valid_email_info(valid_participants)
    valid_email_dict = create_valid_email_dict(valid_email)
    merge_valid_email(participant_data, valid_email_dict)

    # Add catch-all flags
    participant_data = add_catch_all_flag(participant_data, catch_all_domains)

    # Save updated participant data to JSON
    save_json(participant_data, RESULTS_FILE)
    print(f"Updated participant data saved to {RESULTS_FILE}")

    # Upload to MongoDB
    collection = connect_to_mongodb()
    delete_existing_collection(collection)
    upload_to_mongodb(collection, RESULTS_FILE)

# === Run ===

if __name__ == "__main__":
    participant_data_json = "participant_data.json"
    participant_data_email_json = "email_verification_results.json"
    process_data(participant_data_json, participant_data_email_json)
