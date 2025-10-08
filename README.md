# MarketingPulse-Scraper-Email-Validator
Python tool to scrape participant data from the MarketingPulse site, generate potential emails using Vertex AI, and validate them via DNS + SMTP checks. Built with BeautifulSoup, pandas, tqdm, and pymongo. Outputs verified emails and uploads results to MongoDB.

It is designed to:

Collect participant information (name, title, company, country, etc.) from multiple pages.

Match company names with known domains.

Generate likely email addresses using Vertex AI.

Validate those emails through DNS and SMTP checks.

Upload the verified dataset to a MongoDB collection.
