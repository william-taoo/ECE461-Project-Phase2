"""
Tests for URL_handler.

These tests confirm that URLHandler correctly recognizes different URL types
and groups sequences of URLs into Model instances with associated code/dataset links.
"""

import pytest
from URL_handler import URLHandler

def test_is_github_url() -> None:
    """Tests GitHub URL identification."""
    assert URLHandler.is_github_url("https://github.com/SkyworkAI/Matrix-Game") == True
    assert URLHandler.is_github_url("https://huggingface.co/google/gemma") == False

def test_is_huggingface_dataset() -> None:
    """Tests Hugging Face dataset URL identification."""
    assert URLHandler.is_huggingface_dataset("https://huggingface.co/datasets/xlangai/AgentNet") == True
    assert URLHandler.is_huggingface_dataset("https://huggingface.co/google/gemma") == False

def test_is_huggingface_model() -> None:
    """Tests Hugging Face model URL identification."""
    assert URLHandler.is_huggingface_model("https://huggingface.co/google/gemma-3-270m/tree/main") == True
    assert URLHandler.is_huggingface_model("https://huggingface.co/datasets/xlangai/AgentNet") == False

def test_process_urls_full_set() -> None:
    """Tests processing a list with a dataset, code, and model URL."""
    urls = [
        "https://huggingface.co/datasets/xlangai/AgentNet",
        "https://github.com/SkyworkAI/Matrix-Game",
        "https://huggingface.co/google/gemma-3-270m/tree/main"
    ]
    models = URLHandler.process_urls(urls)
    assert len(models) == 1
    assert models[0].url == "https://huggingface.co/google/gemma-3-270m/tree/main"
    assert models[0].dataset.dataset_url == "https://huggingface.co/datasets/xlangai/AgentNet"
    assert models[0].code.code_url == "https://github.com/SkyworkAI/Matrix-Game"

def test_process_urls_model_only() -> None:
    """Tests processing a list with only a model URL."""
    urls = ["https://huggingface.co/bert-base-uncased"]
    models = URLHandler.process_urls(urls)
    assert len(models) == 1
    assert models[0].url == "https://huggingface.co/bert-base-uncased"
    assert models[0].dataset.dataset_url is None
    assert models[0].code.code_url is None
