import pytest
from unittest.mock import MagicMock
import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CustomObjects.Model import Model

@pytest.fixture
def model():
    """Set up a new Model instance for each test."""
    return Model(model_url="http://example.com/model",
                 dataset_url="http://example.com/dataset",
                 code_url="http://example.com/code")

def test_compute_net_score(model):
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
    net_score = model.compute_net_score()

    # Check if the computed score is as expected
    assert abs(net_score - expected_net_score) < 1e-3

def test_concurrency_in_compute_net_score(model):
    """Test that attribute-getting functions are called concurrently."""
    sleep_time = 0.1  # seconds
    num_functions = 7

    # This helper function will be the side effect for our mocks
    def mock_side_effect(*args, **kwargs):
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
    model.compute_net_score()
    end_time = time.time()

    total_time = end_time - start_time
    
    # If the functions ran sequentially, total_time would be ~ sleep_time * num_functions
    # If they ran concurrently, total_time should be just over sleep_time
    assert total_time < sleep_time * num_functions
    assert total_time > sleep_time