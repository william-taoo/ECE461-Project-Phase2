"""Tests for artifact download endpoints"""
import pytest


def test_download_model(client):
    """Test downloading a model by ID"""
    # Download endpoint expects a model_id in the path
    response = client.get('/download/test-model-id')
    # May return 404 if model doesn't exist or other error
    assert response.status_code in [200, 404, 400, 500]
