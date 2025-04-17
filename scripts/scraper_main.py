import json

from llm import LLMScraper
from scraper import web_scraper

web_scraper()

def fetch_llm_results(professor_info):
    llm_scraper = LLMScraper(professor_info)

    professor_info["research_areas"] = {
        "scraping": professor_info.get("research_areas", []),
        "deepseek": llm_scraper.clean_result_string(llm_scraper.deepseek_for_info()),
        "chatgpt": llm_scraper.clean_result_string(llm_scraper.chatGPT_for_info()),
        "mistral": llm_scraper.clean_result_string(llm_scraper.mistral_for_info()),
        "llama": llm_scraper.clean_result_string(llm_scraper.llama_for_info())
    }

    return professor_info

with open("results.json", "r") as f:
    data = json.load(f)

updated_data = [fetch_llm_results(professor_info) for professor_info in data]

with open("results.json", "w") as f:
    json.dump(updated_data, f, indent=4)
