import subprocess
import json
import requests
import time

class OpenSourceLLM():
    def __init__(self, professor):
         self.serpapi_key = "ADD SERP KEY"
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
        
    def get_prof_info(self):
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
                print(result.stdout)
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
                print(result.stdout)
                return(result.stdout)
            else:
                print(f"Error running Ollama: {result.stderr}")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    llm = OpenSourceLLM("Mustaque Ahamad")
    result = llm.llama_for_info()



