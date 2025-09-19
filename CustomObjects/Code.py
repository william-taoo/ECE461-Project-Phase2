class Code:
    url: str
    quality: float
    code_availability: int

    def __init__(self, url: str) -> None:
        self.url = url
        self.quality = 0.0
        self.code_availability = 0 if url is None else 1

    def get_quality(self) -> float:
        #TODO implement quality assessment logic
        return 1.0