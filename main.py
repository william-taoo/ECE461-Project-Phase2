import sys
from URL_handler import URLHandler

def main():
    #TODO get URLs from command line arguments
    url_file_path = sys.argv[1]

    with open(url_file_path, 'r') as f:
        urls = f.readlines()

    # Process URLs and create Model objects
    models = URLHandler.process_urls(urls)

    # Compute scores and print output for each model
    for model in models:
        model.compute_net_score()
        print(f"URL: {model.url}, Net Score: {model.net_score:.2f}")


if __name__ == "__main__":
    main()