from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests

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

statistics_data = []
google_scholar_details = fetch_google_scholar_details("Ling Liu", "Georgia Institute of Technology")
if google_scholar_details:
    google_scholar_link, google_scholar_id = google_scholar_details

    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}
    google_scholar_page = requests.get(google_scholar_link, headers=headers)
    soup = BeautifulSoup(google_scholar_page.content, 'html.parser')
    table = soup.find('table', id='gsc_rsb_st')

    rows = table.find_all('tr')
    for row in rows:
        data_element = row.find_all('td', class_='gsc_rsb_std')
        for datum in data_element:
            if not statistics_data:
                statistics_data = [datum.get_text(), ]
            else:
                statistics_data.append(datum.get_text())

    research_areas = soup.find('div', class_='gsc_prf_il', id='gsc_prf_int')
    research_area_links = research_areas.find_all('a')
    research_areas = []
    for link in research_area_links:
        research_areas.append(link.get_text().lower())
    print(research_areas)
else:
    google_scholar_link, google_scholar_id = None, None

print(statistics_data)
print(google_scholar_link)
print(google_scholar_id)