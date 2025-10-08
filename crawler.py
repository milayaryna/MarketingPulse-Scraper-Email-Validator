from bs4 import BeautifulSoup
import requests
import json
import numpy as np  # For handling NaN values

# Initialize the list to store all participant data
result_data = []

# Loop through each page (1 to 104)
for page_num in range(1, 105):  # Pages 1 to 104
    print(f"Scraping page {page_num}...")
    url = f"https://marketingpulse.hktdc.com/conference/mp/en/participant-list?pageNum={page_num}&pageSize=30"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    # Combine base URL with detail links
    head = "https://marketingpulse.hktdc.com"
    links = soup.find_all("a", class_="text-level-caption ParticipantsList_detailBtn__3ufS_")
    page_links = []
    for i in links:
        href = i.get('href')
        if href:  # Ensure href is not None
            full_url = head + href
            page_links.append(full_url)

    # Iterate through each detail link to scrape participant information
    for url_inner in page_links:
        res_inner = requests.get(url_inner)
        soup_inner = BeautifulSoup(res_inner.text, 'html.parser')

        # Initialize a dictionary for participant data with default NaN values
        data = {
            "name": np.nan,
            "title": np.nan,
            "company": np.nan,
            "country_region": np.nan,
            "nature_of_business": np.nan,
            "interested_in": np.nan
        }

        # Extract personal information (name, title, company)
        info_card = soup_inner.find("div", class_="detail_page_participantInfo__vJ6lR")
        if info_card:
            data["name"] = info_card.find("div", class_="ParticipantCard_title__PRR3S").get_text(strip=True) if info_card.find("div", class_="ParticipantCard_title__PRR3S") else np.nan
            data["title"] = info_card.find("div", class_="ParticipantCard_text__xOTjb").get_text(strip=True) if info_card.find("div", class_="ParticipantCard_text__xOTjb") else np.nan
            data["company"] = info_card.find("div", class_="participant-card-sub-text").get_text(strip=True) if info_card.find("div", class_="participant-card-sub-text") else np.nan

        # Extract additional information (country, nature of business, interests)
        answer_cards = soup_inner.find_all("div", class_="ParticipantCard_card__3DQwD")
        for card in answer_cards:
            title = card.find("div", class_="ParticipantCard_title__PRR3S").get_text(strip=True) if card.find("div", class_="ParticipantCard_title__PRR3S") else None
            if title == "Country / Region":
                data["country_region"] = card.find("ul").get_text(strip=True) if card.find("ul") else np.nan
            elif title == "Nature of Business":
                subheader = card.find("div", class_="ParticipantCard_text__xOTjb").get_text(strip=True) if card.find("div", class_="ParticipantCard_text__xOTjb") else ""
                details = [li.get_text(strip=True) for li in card.find_all("li")] if card.find_all("li") else []
                data["nature_of_business"] = [subheader] + details if subheader or details else np.nan
            elif title == "Interesed In":
                data["interested_in"] = [li.get_text(strip=True) for li in card.find_all("li")] if card.find_all("li") else np.nan

        # Append the participant data to the result list
        result_data.append(data)

# Save all the scraped data to a JSON file
output_file = "participant_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=4)

# Print completion message and show the first 5 records as an example
print(f"All data has been saved to {output_file}!")
print(json.dumps(result_data[:5], ensure_ascii=False, indent=4))  # Display the first 5 records as a preview
