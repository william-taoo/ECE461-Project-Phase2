import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "../../backend")
sys.path.insert(0, backend_path)

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    # Create a temporary registry file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_registry_path = f.name
        json.dump({}, f)
    
    app.config['TESTING'] = True
    app.config['REGISTRY_PATH'] = temp_registry_path
    
    with app.test_client() as test_client:
        yield test_client
    
    # Clean up temp file
    if os.path.exists(temp_registry_path):
        os.remove(temp_registry_path)


@pytest.fixture
def registry_with_artifact(client):
    """Create a test registry with a sample artifact."""
    sample_artifact = {
        "test-id-123": {
            "metadata": {
                "id": "test-id-123",
                "name": "test-model",
                "type": "model",
                "version": "1.0.0"
            },
            "data": {
                "url": "https://example.com/model"
            }
        }
    }
    
    registry_path = app.config['REGISTRY_PATH']
    with open(registry_path, 'w') as f:
        json.dump(sample_artifact, f)
    
    return client, sample_artifact
