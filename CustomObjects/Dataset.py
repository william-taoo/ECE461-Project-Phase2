class Dataset:
    def __init__(self, url):
        self.url = url
        self.quality = 0
        self.dataset_availability = 0 if url is None else 1

    def get_quality(self):
        #TODO implement quality assessment logic
        return 1