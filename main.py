import sys
import json
import time
from pathlib import Path
from URL_handler import URLHandler
from CLI_parser import read_urls
from dotenv import load_dotenv
import os

def main():
    
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("API_KEY")

    if not api_key:
        print("Error: API_KEY environment variable not set. Make sure it is in your .env file.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) != 2:
        print(f"Usage: ./{os.path.basename(__file__)} URL_FILE", file=sys.stderr)
        sys.exit(1)

    url_file_path = sys.argv[1]
    
    urls = read_urls(Path(url_file_path))

    models = URLHandler.process_urls(urls)

    # Process each model and print its scores
    for model in models:
        name = model.get_name()
        category = model.get_category()
        model.compute_net_score(api_key=api_key)
        
        output_data = {
            "name": name,
            "category": category,
            "net_score": model.net_score,
            "ramp_up_time": model.ramp_up_time,
            "bus_factor": model.bus_factor,
            "performance_claims": model.performance_claims,
            "license": model.license,
            "size_score": model.size_score,
            "dataset_and_code_score": getattr(model, 'dataset_and_code_score', 0.0), 
            "dataset_quality": model.dataset.quality,
            "code_quality": model.code.quality,
        }

        # Print the final JSON object to stdout
        print(json.dumps(output_data))

if __name__ == "__main__":
    main()