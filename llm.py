from openai import OpenAI
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class LLM():
    def __init__(self, professor):
        self.DEEPSEEK_API_KEY = "ADD DEEPSEEK KEY"
        self.CHATGPT_API_KEY = "ADD CHATGPT KEY"
        self.professor = professor
        self.google_scholar_link = None
        self.prof_info = self.get_prof_info()
        self.prompt_v1 = f"""
                        I want to know more about {self.professor} who teaches at Georgia Tech. 
                        Specifically, I want to work under {self.professor} as a Phd or research student. 
                        To know if {self.professor} is the right fit for me, I want to know what kinds of topics they research and focus on. 
                        Return the following in bullet points.
                        Give me 3 titles of research papers that they have authored. 
                        Give me 3 keywords that describe the specific topics or subjects that they research or teach in. 
                        The below is how I want you to format your response. Don't include anything in your response outside of the format shown below.
                        Don't incude anything in your response before or after the format below.
                        Titles:
                            -Paper Title 1
                            -Paper Title 2
                            -Paper Title 3
                        Topics:
                            -Topic 1
                            -Topic 1
                            -Topic 1
                       """
        self.prompt_v2 = f""" 
                        I want to know more about {self.professor} who teaches at Georgia Tech. 
                        Specifically, I want to work under {self.professor} as a Phd or research student. 
                        To know if {self.professor} is the right fit for me, I want to know what kinds of topics they research and focus on. 
                        Return the following in bullet points.
                        Give me the Professor's email.
                        Give me links/urls to their material (When including URLs in your response, include just the urls as bullet points with no additional notes). 
                        Give me titles of research papers that they have authored. 
                        Give me keywords that describe the specific topics or subjects that they research or teach in. 
                        If you can't find information for any of the fields mentioned above just don't include them in your response.
                        Here is some information on {self.professor} to help you with this task {self.prof_info}, 
                        but also feel free to do your own research on {self.professor}.
                        The below is how I want you to format your response. Don't include anything in your response outside of the format shown below.
                        Email:
                            -email
                        Resource Links:
                            -URL 1
                            -URL 2
                            - ...
                        Titles:
                            -Paper Title 1
                            -Paper Title 2
                            -Paper Title 3
                            - ...
                        Topics:
                            -Topic 1
                            -Topic 1
                            -Topic 1
                            - ...

        """
        self.prompt_v3 = f""" 
                        I want to know more about {self.professor} who teaches at Georgia Tech. 
                        Specifically, I want to work under {self.professor} as a Phd or research student. 
                        To know if {self.professor} is the right fit for me, I want to know what kinds of topics they research and focus on. 
                        Return the following in bullet points.
                        Give me the Professor's email.
                        Give me links/urls to their material (When including URLs in your response, include just the urls as bullet points with no additional notes). 
                        Give me titles of research papers that they have authored. 
                        Give me keywords that describe the specific topics or subjects that they research or teach in. 
                        If you can't find information for any of the fields mentioned above just don't include them in your response.
                        To help you find the information I want, look at their google scholar profile page through this url: {self.google_scholar_link}.
                        You should also go through publicly availble infromation on {self.professor} to inform your response. 
                        Also, Here is some information on {self.professor} to help you with this task {self.prof_info}, 
                        The below is how I want you to format your response. Don't include anything in your response outside of the format shown below.
                        Email:
                            -email
                        Resource Links:
                            -URL 1
                            -URL 2
                            - ...
                        Titles:
                            -Paper Title 1
                            -Paper Title 2
                            -Paper Title 3
                            - ...
                        Topics:
                            -Topic 1
                            -Topic 1
                            -Topic 1
                            - ...

        """
    def fetch_google_scholar_html(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode (no GUI)
        options.add_argument('--disable-blink-features=AutomationControlled')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        html = driver.page_source
        driver.quit()
        print(html)
        return html
    
    def get_prof_info(self):
        with open('results.json', 'r') as file:
            data = json.load(file)
        
        for item in data:
            if item.get('name') == self.professor:
                google_scholar_link = item.get('link', {}).get('google_scholar', {}).get('google_scholar_link')
                if google_scholar_link:
                    self.google_scholar_link = google_scholar_link
                return item  
        return None 

    def deepseek_for_info(self):
        prompt = self.prompt_v2
        if self.google_scholar_link:
            prompt = self.prompt_v3
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
        prompt = self.prompt_v2
        if self.google_scholar_link:
            prompt = self.prompt_v3
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
llm.chatGPT_for_info()
