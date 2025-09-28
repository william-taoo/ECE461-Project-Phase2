# URL_Handler.py (Revised)

from typing import List, Tuple, Optional
from CustomObjects.Model import Model # Your Model class

class URLHandler:
    @staticmethod
    def process_urls(model_definitions: List[Tuple[Optional[str], Optional[str], str]]) -> List[Model]:
        """
        Processes a list of model definitions to create Model objects.

        Args:
            model_definitions: A list of tuples, each containing
                               (code_url, dataset_url, model_url).
        
        Returns:
            A list of instantiated Model objects.
        """
        models: List[Model] = []
        
        for code_url, dataset_url, model_url in model_definitions:
            model = Model(
                model_url=model_url,
                dataset_url=dataset_url,
                code_url=code_url
            )
            models.append(model)
            
        return models