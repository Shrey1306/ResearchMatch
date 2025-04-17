from openai import OpenAI
import requests
import subprocess

class LLMScraper():
    def __init__(self, professor_info):
        self.serpapi_key = "ADD SERP KEY"
        self.DEEPSEEK_API_KEY = "ADD DEEPSEEK KEY"
        self.CHATGPT_API_KEY = "ADD CHATGPT KEY"

        self.prof_info = professor_info
        self.professor = professor_info.get('name')

        self.google_scholar_link = None
        google_scholar_link = professor_info.get('link', {}).get('google_scholar', {}).get('google_scholar_link')
        if google_scholar_link:
            self.google_scholar_link = google_scholar_link

        self.google_scholar_id = None
        google_scholar_id = professor_info.get('link', {}).get('google_scholar', {}).get('google_scholar_id')
        if google_scholar_id:
            self.google_scholar_id = google_scholar_id

        self.google_scholar_html = self.get_google_scholar_html(self.google_scholar_id)

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
    
    def get_google_scholar_html(self, scholar_user_id):
        """Uses SerpAPI to get Google Scholar profile data based on scholar user ID."""
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
    
    def deepseek_for_info(self):
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

        # print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def chatGPT_for_info(self):
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
        # print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def mistral_for_info(self):
        try:
            result = subprocess.run(
                ['ollama', 'run', 'mistral'], 
                input=self.prompt,           
                capture_output=True,           
                text=True                     
            )

            # Check if the command was successful
            if result.returncode == 0:
                # print(result.stdout)
                return(result.stdout)
            else:
                print(f"Error running Ollama: {result.stderr}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def llama_for_info(self):
        try:
            result = subprocess.run(
                ['ollama', 'run', 'llama3.2'], 
                input=self.prompt,           
                capture_output=True,           
                text=True                     
            )

            # Check if the command was successful
            if result.returncode == 0:
                # print(result.stdout)
                return(result.stdout)
            else:
                print(f"Error running Ollama: {result.stderr}")

        except Exception as e:
            print(f"An error occurred: {e}")
    
    def clean_result_string(self, results):
        if not results:
            return []
        
        results = results.strip()  # Remove leading/trailing whitespace
        prefix = "Research Areas:"

        if results.startswith(prefix):
            topics_str = results[len(prefix):].strip()
            if topics_str:
                return [topic.strip().lower() for topic in topics_str.split(",") if topic.strip()]
        
        return []