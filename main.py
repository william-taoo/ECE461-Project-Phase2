import sys
from pathlib import Path
from URL_handler import URLHandler
from CLI_parser import read_urls

def main():
    url_file_path = sys.argv[1]

    # Read and clean URLs from filepath given in command line argument
    urls = read_urls(Path(url_file_path))
    
    # for debugging
    # print(urls)

    # Process URLs and create Model objects
    models = URLHandler.process_urls(urls)

    # for debugging
    # print(models)

    # Compute scores and print output for each model
    for model in models:
        print(model.get_size())
        
        # print(f"URL: {model.url}, Net Score: {model.net_score:.2f}")


if __name__ == "__main__":
    main()