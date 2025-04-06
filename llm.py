from openai import OpenAI
import requests

class LLM():
    def __init__(self, professor):
        # self.DEEPSEEK_API_KEY = "ADD DEEPSEEK KEY"
        # self.CHATGPT_API_KEY = "ADD CHATGPT KEY"
        self.professor = professor
        self.prompt = f"""I want to know more about {self.professor} who teaches at Georgia Tech. 
                          Specifically, I want to work under {self.professor} as a Phd or research student. 
                          To know if {self.professor} is the right fit for me, I want to know what kinds of topics they research and focus on. 
                          Return the following in bullet points.
                          Give me 3 titles of research papers that they have authored. 
                          Give me 3 keywords that describe the specific topics or subjects that they research or teach in. 
                          The below is how I want you to format your response. Don't include anything in your response outside of the format shown below.
                          Titles:
                            -Paper Title 1
                            -Paper Title 2
                            -Paper Title 3
                          Topics:
                            -Topic 1
                            -Topic 1
                            -Topic 1
                       """

    def deepseek(self):
        client = OpenAI(api_key=self.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": self.prompt},
            ],
            stream=False
        )

        print(response.choices[0].message.content)

    def chatGPT(self):
        client = OpenAI(api_key=self.CHATGPT_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": self.prompt},
            ],
            stream=False
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    

llm = LLM("Gregory Abowd")
llm.chatGPT()

