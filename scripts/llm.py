from openai import OpenAI
import requests
import json


class LLM():
    """
    Class for interacting with various LLM APIs to analyze professor research areas.
    """
    def __init__(self, professor):
        self.serpapi_key = "ADD SERP KEY"
        self.DEEPSEEK_API_KEY = "ADD DEEPSEEK KEY"
        self.CHATGPT_API_KEY = "ADD CHATGPT KEY"
        self.professor = professor
        self.google_scholar_link = None
        self.google_scholar_id = None
        self.prof_info = self.get_prof_info()
        self.google_scholar_html = self.get_html(self.google_scholar_id)

        self.prompt = f""" 
                        I want to work under {self.professor} as a Phd or research student. 
                        To know if {self.professor} is the right fit for me, I want to know what kinds of topics they research and focus on. 
                        Give me keywords that describe the specific topics or subjects that they research or teach in. 
                        To help you find the information I want, here is the html representation of their google scholar page:

                        {self.google_scholar_html}

                        The below is how I want you to format your response. Don't include anything in your response outside of the format shown below.
                        Your response should just be a single line. It should just have "Research Areas: " once, followed by a list of the keywords you determined separated by commas as shown below.
                        Research Areas: Topic 1, Topic 2, Topic 3, ... 

        """
    
    def get_html(self, scholar_user_id):
        """
        Get Google Scholar profile data using SerpAPI.
        
        Args:
            scholar_user_id: Google Scholar user ID
            
        Returns:
            JSON response from SerpAPI
        """
        try:
            url = "https://serpapi.com/search"
            params = {
                "engine": "google_scholar_author",
                "author_id": scholar_user_id,
                "api_key": self.serpapi_key
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                return f"Error: {response.status_code} - {response.reason}"
        except Exception as e:
            return f"An error occurred: {e}"
    
    def get_prof_info(self):
        """
        Get professor information from results.json.
        
        Returns:
            Professor data entry or None if not found
        """
        with open('results.json', 'r') as file:
            data = json.load(file)
        
        for item in data:
            if item.get('name') == self.professor:
                google_scholar_link = item.get('link', {}).get('google_scholar', {}).get('google_scholar_link')
                if google_scholar_link:
                    self.google_scholar_link = google_scholar_link

                google_scholar_id = item.get('link', {}).get('google_scholar', {}).get('google_scholar_id')
                if google_scholar_id:
                    self.google_scholar_id = google_scholar_id
                return item  
        return None 

    def deepseek_for_info(self):
        """
        Get research areas using DeepSeek API.
        
        Returns:
            Research areas as comma-separated string
        """
        prompt = self.prompt
        client = OpenAI(api_key=self.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def chatGPT_for_info(self):
        """
        Get research areas using ChatGPT API.
        
        Returns:
            Research areas as comma-separated string
        """
        prompt = self.prompt
        client = OpenAI(api_key=self.CHATGPT_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content

llm = LLM("Mustaque Ahamad")
llm.deepseek_for_info()