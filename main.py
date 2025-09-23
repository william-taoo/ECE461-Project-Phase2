import sys
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
        raise ValueError("Error: API_KEY environment variable not set! Make sure it is in your .env file.")

    url_file_path = sys.argv[1]

    # Read and clean URLs from filepath given in command line argument
    urls = read_urls(Path(url_file_path))

    # for debugging
    # print(urls)

    # Process URLs and create Model objects
    models = URLHandler.process_urls(urls)

    # for debugging
    # print(models)

    # Compute code quality scores and print output for each model
    for model in models:
        score = model.compute_net_score(api_key=api_key)
        print(f"Model: {model.url}")
        print(f"  Size score: {model.size_score}")
        print(f"  License: {model.license}")
        print(f"  Ramp-up time: {model.ramp_up_time}")
        print(f"  Bus factor: {model.bus_factor}")
        print(f"  Dataset quality: {model.dataset.quality}")
        print(f"  Dataset availability: {model.dataset.dataset_availability}")
        print(f"  Code quality: {model.code.quality}")
        print(f"  Code availability: {model.code.code_availability}")
        print(f"  Performance claims: {model.performance_claims}")
        print(f"  Net score: {score}\n")

if __name__ == "__main__":
    main()