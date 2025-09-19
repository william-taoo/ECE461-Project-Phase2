import boto3
import json

class LLMQuerier:
    def __init__(self, endpoint_name, aws_region):
        self.endpoint_name = endpoint_name
        self.aws_region = aws_region
        self.sagemaker_runtime = boto3.client(
            "sagemaker-runtime", 
            region_name=self.aws_region
        )

    def query(self, prompt, max_new_tokens=512, top_p=0.9, temperature=0.6):
        payload = {
            "inputs": [
                [
                    {"role": "user", "content": prompt}
                ]
            ],
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "top_p": top_p,
                "temperature": temperature,
                "return_full_text": False
            }
        }

        try:
            payload_str = json.dumps(payload)
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=payload_str,
            )
            result = json.loads(response["Body"].read().decode())
            return result[0]["generation"]["content"].strip()
        except Exception as e:
            print(f"An error occurred: {e}")
            return None