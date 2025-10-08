# MarketingPulse-Scraper-Email-Validator  

Python tool to scrape participant data from the **MarketingPulse** site, generate potential emails using **Vertex AI**, and validate them via **DNS + SMTP checks**.  
Built with **BeautifulSoup**, **pandas**, **tqdm**, and **pymongo**. Outputs verified emails and uploads results to **MongoDB**.

---

## Features
- Collect participant information (name, title, company, country, etc.) from multiple pages  
- Match company names with known domains  
- Generate likely email addresses using Vertex AI  
- Validate emails through DNS and SMTP checks  
- Upload verified dataset to MongoDB  

---

## 1. Web Scraping (BeautifulSoup)
- Iterates through 104 pages of participant lists  
- Extracts:
  - Name  
  - Title  
  - Company  
  - Country / Region  
  - Nature of Business  
  - Interested In  
- Saves data into `participant_data.json`

---

## 2. Vertex AI Integration
- Prompts user to upload Vertex AI credentials (`.json`)  
- Initializes the **gemini-1.5-pro** model  
- Generates probable email formats (e.g. `firstname.lastname@domain.com`) using participant and historical data  

---

## 3. Email Validation
Each generated email undergoes a 3-step validation process:
1. **Syntax check** – verifies format with regex  
2. **DNS check** – confirms MX records exist  
3. **SMTP verification** – tests handshake with mail server  

Additional features:
- Detects and flags **catch-all domains**  
- Excludes invalid or unreachable emails  

