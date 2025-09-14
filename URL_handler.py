from typing import List, Optional, Tuple
from CustomObjects.Model import Model

class URLHandler:

    @staticmethod
    def is_github_url(url: str) -> bool:
        return 'github.com' in url

    @staticmethod
    def is_huggingface_dataset(url: str) -> bool:
        return 'huggingface.co/datasets/' in url

    @staticmethod
    def is_huggingface_model(url: str) -> bool:
        return 'huggingface.co' in url and not URLHandler.is_huggingface_dataset(url)

    @staticmethod
    def process_urls(urls: List[str]) -> List[Model]:

        models: List[Model] = []
        current_dataset_url: Optional[str] = None
        current_code_url: Optional[str] = None

        for url in urls:
            url = url.strip()
            if not url:
                continue

            if URLHandler.is_github_url(url):
                current_code_url = url
            elif URLHandler.is_huggingface_dataset(url):
                current_dataset_url = url
            elif URLHandler.is_huggingface_model(url):
                model = Model(
                    model_url=url,
                    dataset_url=current_dataset_url,
                    code_url=current_code_url
                )
                models.append(model)
                
                current_dataset_url = None
                current_code_url = None
            else:
                # Print warning for unknown URL types
                print(f"Warning: Unknown URL type ignored: {url}")
                
        return models