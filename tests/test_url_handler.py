"""
Tests for URL_handler.

These tests confirm that URLHandler correctly takes a structured list of 
(code_url, dataset_url, model_url) tuples and creates Model instances.
"""

import pytest
from URL_handler import URLHandler
from CustomObjects.Model import Model  
class MockModel:
    def __init__(self, model_url=None, dataset_url=None, code_url=None):
        self.model_url = model_url
        self.dataset_url = dataset_url
        self.code_url = code_url

def test_process_urls_full_set(monkeypatch) -> None:
    """Tests processing a tuple with code, dataset, and model URLs."""
    monkeypatch.setattr("URL_handler.Model", MockModel)
    
    definitions = [
        ("https://github.com/a/b", "https://dataset.com/c/d", "https://model.com/e/f")
    ]
    
    models = URLHandler.process_urls(definitions)
    
    assert len(models) == 1
    assert models[0].model_url == "https://model.com/e/f"
    assert models[0].dataset_url == "https://dataset.com/c/d"
    assert models[0].code_url == "https://github.com/a/b"

def test_process_urls_model_only(monkeypatch) -> None:
    """Tests processing a tuple with only a model URL."""
    monkeypatch.setattr("URL_handler.Model", MockModel)
    
    definitions = [(None, None, "https://model.com/just-model")]
    
    models = URLHandler.process_urls(definitions)
    
    assert len(models) == 1
    assert models[0].model_url == "https://model.com/just-model"
    assert models[0].dataset_url is None
    assert models[0].code_url is None

def test_process_urls_handles_multiple_models(monkeypatch) -> None:
    """Tests processing a list with multiple, varied model definitions."""
    monkeypatch.setattr("URL_handler.Model", MockModel)

    definitions = [
        ("https://code1", "https://dataset1", "https://model1"),
        (None, "https://dataset1", "https://model2"), # Shared dataset
        ("https://code3", None, "https://model3"),    # No dataset
    ]

    models = URLHandler.process_urls(definitions)

    assert len(models) == 3
    # Check model 1
    assert models[0].model_url == "https://model1"
    assert models[0].dataset_url == "https://dataset1"
    assert models[0].code_url == "https://code1"
    # Check model 2
    assert models[1].model_url == "https://model2"
    assert models[1].dataset_url == "https://dataset1"
    assert models[1].code_url is None
    # Check model 3
    assert models[2].model_url == "https://model3"
    assert models[2].dataset_url is None
    assert models[2].code_url == "https://code3"

def test_process_urls_empty_input() -> None:
    """Tests that an empty list of definitions results in an empty list of models."""
    definitions = []
    models = URLHandler.process_urls(definitions)
    assert models == []