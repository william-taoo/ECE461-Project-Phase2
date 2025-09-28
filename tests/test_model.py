"""
Tests for CustomObjects.Model.

These tests exercise the Model scoring pipeline and helpers:
 - individual metric retrieval methods (size, license, bus factor, ramp-up)
 - integration/combination logic in compute_net_score
 - concurrency behaviour to ensure metric getters run in parallel
 - LLM-dependent methods are mocked to avoid network calls
"""

from __future__ import annotations
import pytest
from unittest.mock import MagicMock
import sys
import os
import time
from typing import Tuple, Any
from types import SimpleNamespace
from datetime import datetime, timedelta
from CustomObjects.Model import Model

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def model() -> Model:
    """Set up a new Model instance for each test."""
    return Model(model_url="http://example.com/model",
                 dataset_url="http://example.com/dataset",
                 code_url="http://example.com/code")

def test_compute_net_score(model: Model) -> None:
    """Test that the net score is computed correctly."""
    # Mock the methods that would perform external actions
    model.get_size = MagicMock(return_value=1)
    model.get_license = MagicMock(return_value=1)
    model.get_ramp_up_time = MagicMock(return_value=1)
    model.get_bus_factor = MagicMock(return_value=1)
    model.dataset.get_quality = MagicMock(return_value=1)
    model.code.get_quality = MagicMock(return_value=1)
    model.get_performance_claims = MagicMock(return_value=1)
    
    # Mock availability attributes
    model.dataset.dataset_availability = 1
    model.code.code_availability = 1

    # The expected score is the sum of all weights, since all metric values are 1
    expected_net_score = 0.25 + 0.05 + 0.15 + 0.195 + 0.025 + 0.005 + 0.025 + 0.30
    
    # Compute the net score
    net_score = model.compute_net_score(api_key="dummy_key")

    # Check if the computed score is as expected
    assert abs(net_score - expected_net_score) < 1e-3

def test_concurrency_in_compute_net_score(model: Model) -> None:
    """Test that attribute-getting functions are called concurrently."""
    sleep_time = 0.1  # seconds
    num_functions = 7

    # This helper function will be the side effect for our mocks
    def mock_side_effect(*args: Any, **kwargs: Any) -> int:
        time.sleep(sleep_time)
        return 1

    # Mock the methods to simulate work
    model.get_size = MagicMock(side_effect=mock_side_effect)
    model.get_license = MagicMock(side_effect=mock_side_effect)
    model.get_ramp_up_time = MagicMock(side_effect=mock_side_effect)
    model.get_bus_factor = MagicMock(side_effect=mock_side_effect)
    model.dataset.get_quality = MagicMock(side_effect=mock_side_effect)
    model.code.get_quality = MagicMock(side_effect=mock_side_effect)
    model.get_performance_claims = MagicMock(side_effect=mock_side_effect)

    # Mock availability attributes
    model.dataset.dataset_availability = 1
    model.code.code_availability = 1

    start_time = time.time()
    model.compute_net_score(api_key="dummy_key")
    end_time = time.time()

    total_time = end_time - start_time
    
    # If the functions ran sequentially, total_time would be ~ sleep_time * num_functions
    # If they ran concurrently, total_time should be just over sleep_time
    assert total_time < sleep_time * num_functions
    assert total_time > sleep_time


def test_get_name_and_category_and_time_metric() -> None:
    m = Model(model_url="https://huggingface.co/owner/model", dataset_url=None, code_url=None)
    assert m.get_name() == "model"
    assert m.get_category() == "MODEL"

    m2 = Model(model_url='', dataset_url='d', code_url='c')
    assert m2.get_category() == 'DATASET'

    m3 = Model(model_url='', dataset_url='', code_url='c')
    assert m3.get_category() == 'CODE'

    res, lat = m._time_metric(lambda: 123)
    assert res == 123
    assert isinstance(lat, int)


def test_get_size_and_license_and_bus_factor(monkeypatch: Any, tmp_path: str) -> None:
    # get_size: simulate HfApi throwing to exercise the exception branch
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url=None, code_url=None)
    class BadApi:
        def model_info(self, repo_id: str) -> RuntimeError:
            raise RuntimeError('fail')
    monkeypatch.setattr('CustomObjects.Model.HfApi', lambda: BadApi())
    assert m.get_size() == {}

    # get_license: no license heading -> 0.0
    class Api:
        def hf_hub_download(self, repo_id: str, filename: str) -> str:
            fp = tmp_path / 'README.md'
            fp.write_text('no license here')
            return str(fp)
    monkeypatch.setattr('CustomObjects.Model.HfApi', lambda: Api())
    assert m.get_license() == 0.0

    # get_bus_factor: if commits iterator is empty / raises, should return 0.0
    monkeypatch.setattr('CustomObjects.Model.list_repo_commits', lambda repo_id: (_ for _ in ()))
    assert m.get_bus_factor() == 0.0


def test_llm_dependent_methods(monkeypatch: Any) -> None:
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url=None, code_url=None)
    class Q:
        def __init__(self, endpoint: str, api_key: str=None) -> None:
            pass
        def query(self, prompt: str) -> str:
            return '0.6'
    monkeypatch.setattr('CustomObjects.Model.LLMQuerier', Q)
    assert m.get_ramp_up_time(api_key='k') == 0.6
    assert m.get_performance_claims(api_key='k') == 0.6

def make_sibling(size: int) -> SimpleNamespace:
    return SimpleNamespace(size=size)

def test_get_size_small_and_large(monkeypatch: Any) -> None:
    # small total size -> all device scores 1.0 except aws_server
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url=None, code_url=None)
    class ApiSmall:
        def model_info(self, repo_id: str, files_metadata: bool = True) -> SimpleNamespace:
            return SimpleNamespace(siblings=[make_sibling(10), make_sibling(20)])
    monkeypatch.setattr('CustomObjects.Model.HfApi', lambda: ApiSmall())
    scores = m.get_size()
    assert scores['raspberry_pi'] == 1.0
    assert scores['jetson_nano'] == 1.0
    assert scores['desktop_pc'] == 1.0
    assert scores['aws_server'] == 1.0

    # large total size -> produce decreased scores for smaller devices
    class ApiLarge:
        def model_info(self, repo_id: str, files_metadata: bool = True) -> SimpleNamespace:
            # set total_size to > 2*raspberry threshold to force 0.0
            large = 3 * (1 * 1024**3)
            return SimpleNamespace(siblings=[make_sibling(large)])
    monkeypatch.setattr('CustomObjects.Model.HfApi', lambda: ApiLarge())
    scores2 = m.get_size()
    assert scores2['raspberry_pi'] <= 0.0
    assert scores2['aws_server'] == 1.0


def test_get_license_with_license_section(monkeypatch: Any, tmp_path: str) -> None:
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url=None, code_url=None)
    # Create README with License heading and MIT
    fp = tmp_path / 'README.md'
    fp.write_text('# Title\n\n## License\nMIT\n\n## Other\nstuff\n')
    class Api:
        def hf_hub_download(self, repo_id: str, filename: str) -> str:
            return str(fp)
    monkeypatch.setattr('CustomObjects.Model.HfApi', lambda: Api())
    assert m.get_license() == 1.0

    # README without license -> 0.0
    fp2 = tmp_path / 'README2.md'
    fp2.write_text('# No license here')
    class Api2:
        def hf_hub_download(self, repo_id: str, filename: str) -> str:
            return str(fp2)
    monkeypatch.setattr('CustomObjects.Model.HfApi', lambda: Api2())
    assert m.get_license() == 0.0


def test_get_bus_factor_happy_path(monkeypatch: Any) -> None:
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url=None, code_url=None)
    # Create commits with created_at within year_limit and authors
    now = datetime.now().astimezone()
    class Commit:
        def __init__(self, created_at: datetime, authors: list[str]) -> None:
            self.created_at = created_at
            self.authors = authors
    # create 20 commits with various authors
    commits = []
    authors = ['a', 'b', 'c']
    for i in range(20):
        commits.append(Commit(created_at=now - timedelta(days=10), authors=[authors[i % 3]]))
    monkeypatch.setattr('CustomObjects.Model.list_repo_commits', lambda repo_id: commits)
    score = m.get_bus_factor()
    # significant authors count: each author ~7 commits -> contribution ~33% >4% -> count=3 => score=3/10
    assert abs(score - 0.6) < 0.001


def test_get_performance_claims_non_numeric(monkeypatch: Any) -> None:
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url=None, code_url=None)
    class Q:
        def __init__(self, endpoint: str, api_key: str=None) -> None:
            pass
        def query(self, prompt: str) -> str:
            return 'not-a-number'
    monkeypatch.setattr('CustomObjects.Model.LLMQuerier', Q)
    assert m.get_performance_claims(api_key='k') == 0.0


def test_compute_net_score_combination(monkeypatch: any) -> None:
    m = Model(model_url='https://huggingface.co/owner/model', dataset_url='d', code_url='c')
    # monkeypatch metric methods
    m._time_metric = lambda func, *args, **kwargs: (func() if callable(func) else func, 5)

    m.get_size = lambda: {'a': 1.0}
    m.get_license = lambda: 1.0
    m.get_ramp_up_time = lambda api_key=None: 0.5
    m.get_bus_factor = lambda: 0.2
    m.get_performance_claims = lambda api_key=None: 0.3
    m.dataset.get_quality = lambda api_key=None: 0.4
    m.code.get_quality = lambda: 0.6
    m.get_dataset_and_code_score = lambda: 0.5

    # set availability
    m.dataset.dataset_availability = 1.0
    m.code.code_availability = 1.0

    net = m.compute_net_score(api_key='k')
    # compute expected net manually using weights from Model.compute_net_score
    weights = {
        'license': 0.25,
        'ramp_up_time': 0.30,
        'bus_factor': 0.10,
        'dataset_quality': 0.095,
        'code_quality': 0.005,
        'performance_claims': 0.20,
        'dataset_and_code_score': 0.05
    }
    expected = (
        weights['license'] * 1.0 +
        weights['ramp_up_time'] * 0.5 +
        weights['bus_factor'] * 0.2 +
        weights['dataset_quality'] * 0.4 +
        weights['code_quality'] * 0.6 +
        weights['performance_claims'] * 0.3 +
        weights['dataset_and_code_score'] * 0.5
    )
    assert abs(net - expected) < 1e-6