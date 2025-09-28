"""
Tests for CustomObjects.Dataset.

These unit tests cover dataset-related utilities and scoring logic:
 - Hugging Face popularity extraction and robust handling of API errors
 - extracting a "Training Data" section from a model README
 - scoring dataset text via the LLM (mocked)
 - the combined get_quality flow that mixes HF stats and LLM output

Filesystem and network interactions are mocked to keep tests fast and deterministic.
"""

from __future__ import annotations
import pytest
import tempfile
from unittest.mock import MagicMock
from typing import Any
from CustomObjects.Dataset import Dataset

class DummyInfo:
    def __init__(self, downloads: int = 0, likes: int = 0, cardData: Any = None) -> None:
        self.downloads = downloads
        self.likes = likes
        self.cardData = cardData


def test_hf_popularity_score_handles_exceptions(monkeypatch: Any) -> None:
    d = Dataset(dataset_url=None, model_url=None)
    # Force HfApi().dataset_info to raise
    class BadApi:
        def dataset_info(self, repo_id: str) -> RuntimeError:
            raise RuntimeError('fail')
    monkeypatch.setattr('CustomObjects.Dataset.HfApi', lambda: BadApi())
    score = d.hf_popularity_score('owner/repo')
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_extract_training_data_info_non_hf() -> None:
    d = Dataset(dataset_url=None, model_url=None)
    assert d.extract_training_data_info('https://example.com/foo') is None


def test_extract_training_data_info_from_readme(monkeypatch: Any, tmp_path: pytest.TempPathFactory) -> None:
    text = """
            # Model

            Some intro

            ## Training Data
            These are the data used.

            ## Other
            stuff
            """
    readme = tmp_path / 'README.md'
    readme.write_text(text, encoding='utf-8')

    class Api:
        def hf_hub_download(self, repo_id: str, filename: str) -> str:
            return str(readme)
    monkeypatch.setattr('CustomObjects.Dataset.HfApi', lambda: Api())

    d = Dataset(dataset_url=None, model_url='https://huggingface.co/owner/model')
    section = d.extract_training_data_info(d.model_url)
    assert 'Training Data' in section


def test_score_with_llm_returns_zero_on_none(monkeypatch: Any) -> None:
    d = Dataset(dataset_url=None, model_url=None)
    class Q:
        def __init__(self, endpoint: str, api_key: str=None) -> None:
            pass
        def query(self, prompt: str) -> None:
            return None
    monkeypatch.setattr('CustomObjects.Dataset.LLMQuerier', Q)
    assert d.score_with_llm('text', api_key='k') == 0.0


def test_get_quality_combination(monkeypatch: Any) -> None:
    # Setup: dataset_url yields popularity; model_url yields section and llm score
    text = """
            # Model

            ## Training Data
            some training data text
            """
    readme = tempfile.NamedTemporaryFile('w', delete=False)
    readme.write(text)
    readme.flush()

    class Api:
        def dataset_info(self, repo_id: str) -> DummyInfo:
            return DummyInfo(downloads=1000000, likes=10000, cardData=None)
        def hf_hub_download(self, repo_id: str, filename: str) -> str:
            return readme.name
    monkeypatch.setattr('CustomObjects.Dataset.HfApi', lambda: Api())

    class Q:
        def __init__(self, endpoint: str, api_key: str=None) -> None:
            pass
        def query(self, prompt: str) -> str:
            return '0.8'
    monkeypatch.setattr('CustomObjects.Dataset.LLMQuerier', Q)

    d = Dataset(dataset_url='https://huggingface.co/datasets/owner/name', model_url='https://huggingface.co/owner/model')
    q = d.get_quality(api_key='k')
    assert 0.0 <= q <= 1.0
