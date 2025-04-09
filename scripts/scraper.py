import re
import time
import random
import requests
import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

NUM_DIRECTORY_PAGES = 24
UNIVERSITY = "Georgia Institute of Technology"
DIRECTORY_BASE_URL = "https://www.cc.gatech.edu/people/faculty?page="
PROFILE_BASE_URL = "https://www.cc.gatech.edu"

all_records = []

for page_number in range(NUM_DIRECTORY_PAGES):
    print("Page Number:", page_number)
    url = DIRECTORY_BASE_URL + str(page_number)
    directory_page = requests.get(url)
    soup = BeautifulSoup(directory_page.content, 'html.parser')
    card_blocks = soup.find_all('div', class_='card-block')

    i = 1
    for card in card_blocks:
        print(i)
        i += 1

        h4_tag = card.find('h4')
        name = h4_tag.get_text(strip=True)
        title = card.find('h6').get_text(strip=True)
        
        a_tag = h4_tag.find('a')
        profile_link = PROFILE_BASE_URL + a_tag['href']

        profile_page = requests.get(profile_link)
        soup = BeautifulSoup(profile_page.content, 'html.parser')
        affiliation_divs = soup.find_all('div', class_='field__item')
        
        affiliations = None
        for affiliation_div in affiliation_divs:
            if "field__item" in affiliation_div['class'][0]:
                a_tag = affiliation_div.find('a')

                if a_tag:
                    if affiliations:
                        affiliations.append(a_tag.get_text(strip=True))
                    else:
                        affiliations = [a_tag.get_text(strip=True), ]

        profile_details = soup.find_all('p', class_='card-block__text')

        email_tag = profile_details[0].find('a')
        email = None
        if email_tag:
            email = email_tag.get_text()

        personal_website_tag = profile_details[1].find('a')
        personal_website = None
        if personal_website_tag:
            personal_website = personal_website_tag.get_text()

        research_areas_text = profile_details[2].get_text()
        research_areas = None
        if len(research_areas_text) > 1:
            research_areas = re.split(r"[,;]\s*", research_areas_text.lstrip("\nResearch Areas:").lower().strip())
        
        def fetch_google_scholar_details(professor_name, university):
            search = DDGS()
            query = f"{professor_name} {university} Google Scholar"
            results = search.text(query, max_results=1)
            for r in results:
                link = r['href']
                if 'https://scholar.google.com/citations?user=' not in link:
                    return
                else:
                    scholar_id = link.split("user=")[1].split("&")[0]
                    return link, scholar_id

        def fetch_orcid_details(professor_name, university):
            search = DDGS()
            query = f"{professor_name} {university} ORCID"
            results = search.text(query, max_results=1)
            for r in results:
                link = r['href']
                if 'https://orcid.org' not in link:
                    return
                else:
                    orcid_id = link.split(".org/")[1]
                    return link, orcid_id

        statistics_data = None
        google_scholar_research_areas = None
        google_scholar_details = fetch_google_scholar_details(name, UNIVERSITY)
        if google_scholar_details:
            google_scholar_link, google_scholar_id = google_scholar_details

            headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}
            google_scholar_page = requests.get(google_scholar_link, headers=headers)
            soup = BeautifulSoup(google_scholar_page.content, 'html.parser')
            table = soup.find('table', id='gsc_rsb_st')

            statistics_data = []
            rows = table.find_all('tr')
            for row in rows:
                data_element = row.find_all('td', class_='gsc_rsb_std')
                for datum in data_element:
                    if not statistics_data:
                        statistics_data = [datum.get_text(), ]
                    else:
                        statistics_data.append(datum.get_text())
            
            google_scholar_research_areas = soup.find('div', class_='gsc_prf_il', id='gsc_prf_int')
            research_area_links = google_scholar_research_areas.find_all('a')
            google_scholar_research_areas = []
            for link in research_area_links:
                google_scholar_research_areas.append(link.get_text().lower())
        else:
            google_scholar_link, google_scholar_id = None, None
        
        orcid_details = fetch_orcid_details(name, UNIVERSITY)
        if orcid_details:
            orcid_link, orcid_id = orcid_details
        else:
            orcid_link, orcid_id = None, None

        if research_areas is not None and google_scholar_research_areas is not None:
            research_areas.extend(google_scholar_research_areas)
        elif research_areas is None and google_scholar_research_areas is not None:
            research_areas = google_scholar_research_areas

        record = {
            "name": name,
            "title": title,
            "email": email,
            "dept_affiliations": affiliations,
            "research_areas": research_areas,
            "link": {
                "profile_link": profile_link,
                "personal_website": personal_website,
                "google_scholar": {
                    "google_scholar_id": google_scholar_id,
                    "google_scholar_link": google_scholar_link
                },
                "orcid": {
                    "orcid_id": orcid_id,
                    "orcid_link": orcid_link
                }
            },
            "statistics": {
                "all": {
                    "citations": statistics_data[0] if statistics_data else 0,
                    "h-index": statistics_data[2] if statistics_data else 0,
                    "i10-index": statistics_data[4] if statistics_data else 0
                },
                "since2020": {
                    "citations": statistics_data[1] if statistics_data else 0,
                    "h-index": statistics_data[3] if statistics_data else 0,
                    "i10-index": statistics_data[5] if statistics_data else 0
                }
            }
        }

        all_records.append(record)
        time.sleep(random.uniform(5, 10))

with open("../public/results.json", "w") as outfile:
    json.dump(all_records, outfile, indent=4)