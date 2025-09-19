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

    def query(self, prompt, max_new_tokens=100, temperature=0.7):
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature
            }
        }


        try:
            payload_str = json.dumps(payload)
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Body=payload_str,
            )
            
            response_str = response["Body"].read().decode()
            # The response from the model is a JSON string within a JSON object.
            # We need to parse it twice.

            result = json.loads(response_str)
            
            # The actual model output is in the 'generation' field of the first item.
            return result["generated_text"].strip().split("\n")[0]
        except Exception as e:
            print(f"An error occurred: {e}")
            return None