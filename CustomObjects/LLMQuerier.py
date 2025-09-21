import boto3
import json
import requests

class LLMQuerier:
    def __init__(self, endpoint, api_key=None):
        self.endpoint = endpoint
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def query(self, prompt, model="llama4:latest"):
        payload = {
            "model": model,
            "messages": [
            {
                "role": "user",
                "content": prompt
            }
            ],
            "stream": False
        }
        try:
            response = requests.post(self.endpoint, headers=self.headers, json=payload)
            if response.status_code == 200:
                data = json.loads(response.content)
                return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"An error occurred: {e}")
            return None