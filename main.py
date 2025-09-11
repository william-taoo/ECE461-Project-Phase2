from CustomObjects import Model

def main():
    #TODO get URLs from command line arguments
    model_url = "http://example.com/model"
    dataset_url = "http://example.com/dataset"
    code_url = "http://example.com/code"

    model = Model(model_url, dataset_url, code_url)
    model.compute_net_score()
    print(f"Net Score: {model.net_score}")


if __name__ == "__main__":
    main()