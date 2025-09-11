import unittest
from unittest.mock import MagicMock
import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CustomObjects.Model import Model

class TestModel(unittest.TestCase):

    def setUp(self):
        """Set up a new Model instance for each test."""
        self.model = Model(model_url="http://example.com/model",
                           dataset_url="http://example.com/dataset",
                           code_url="http://example.com/code")

    def test_compute_net_score(self):
        """Test that the net score is computed correctly."""
        # Mock the methods that would perform external actions
        self.model.get_size = MagicMock(return_value=1)
        self.model.get_license = MagicMock(return_value=1)
        self.model.get_ramp_up_time = MagicMock(return_value=1)
        self.model.get_bus_factor = MagicMock(return_value=1)
        self.model.dataset.get_quality = MagicMock(return_value=1)
        self.model.code.get_quality = MagicMock(return_value=1)
        self.model.get_performance_claims = MagicMock(return_value=1)
        
        # Mock availability attributes
        self.model.dataset.dataset_availability = 1
        self.model.code.code_availability = 1

        # The expected score is the sum of all weights, since all metric values are 1
        expected_net_score = 0.25 + 0.05 + 0.15 + 0.195 + 0.025 + 0.005 + 0.025 + 0.30
        
        # Compute the net score
        net_score = self.model.compute_net_score()

        # Check if the computed score is as expected
        self.assertAlmostEqual(net_score, expected_net_score, places=3)

    def test_concurrency_in_compute_net_score(self):
        """Test that attribute-getting functions are called concurrently."""
        sleep_time = 0.1  # seconds
        num_functions = 7

        # This helper function will be the side effect for our mocks
        def mock_side_effect(*args, **kwargs):
            time.sleep(sleep_time)
            return 1

        # Mock the methods to simulate work
        self.model.get_size = MagicMock(side_effect=mock_side_effect)
        self.model.get_license = MagicMock(side_effect=mock_side_effect)
        self.model.get_ramp_up_time = MagicMock(side_effect=mock_side_effect)
        self.model.get_bus_factor = MagicMock(side_effect=mock_side_effect)
        self.model.dataset.get_quality = MagicMock(side_effect=mock_side_effect)
        self.model.code.get_quality = MagicMock(side_effect=mock_side_effect)
        self.model.get_performance_claims = MagicMock(side_effect=mock_side_effect)

        # Mock availability attributes
        self.model.dataset.dataset_availability = 1
        self.model.code.code_availability = 1

        start_time = time.time()
        self.model.compute_net_score()
        end_time = time.time()

        total_time = end_time - start_time
        
        # If the functions ran sequentially, total_time would be ~ sleep_time * num_functions
        # If they ran concurrently, total_time should be just over sleep_time
        self.assertLess(total_time, sleep_time * num_functions)
        self.assertGreater(total_time, sleep_time)

if __name__ == '__main__':
    unittest.main()