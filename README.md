# MarketingPulse-Scraper-Email-Validator
Python tool to scrape participant data from the MarketingPulse site, generate potential emails using Vertex AI, and validate them via DNS + SMTP checks. Built with BeautifulSoup, pandas, tqdm, and pymongo. Outputs verified emails and uploads results to MongoDB.

It is designed to:

Collect participant information (name, title, company, country, etc.) from multiple pages.

Match company names with known domains.

Generate likely email addresses using Vertex AI.

Validate those emails through DNS and SMTP checks.

Upload the verified dataset to a MongoDB collection.

## Workflow
1. Web Scraping (BeautifulSoup)

Iterates through 104 pages of participant lists.

Extracts fields including:

Name

Title

Company

Country / Region

Nature of Business

Interested In

Saves all data into participant_data.json.

2. Vertex AI Integration

Prompts the user to upload Vertex AI credentials (JSON).

Initializes the gemini-1.5-pro model.

Uses participant and historical customer data to generate probable email formats (e.g. firstname.lastname@domain.com).

3. Email Validation

Each generated email undergoes a 3-step validation process:

Syntax check – verifies format with regex.

DNS check – confirms MX records exist.

SMTP verification – attempts handshake with mail server to test if the address exists.

Additionally:

Catch-all domains are detected and flagged.

Invalid or unreachable emails are excluded.

4. MongoDB Upload

Connects to MongoDB instance:

Drops old collection.

Uploads verified JSON data (participant_data_with_valid_email.json).
