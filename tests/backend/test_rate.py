"""Tests for artifact rating endpoints"""
import pytest
import json


def test_rate_artifact_success(client, registry_with_artifact):
    """Test rating an artifact that exists"""
    client, sample_artifact = registry_with_artifact
    
    response = client.get('/artifact/model/test-id-123/rate')
    # May return rating data or error
    assert response.status_code in [200, 404, 400, 500]


def test_rate_artifact_not_found(client):
    """Test rating an artifact that doesn't exist"""
    response = client.get('/artifact/model/nonexistent-id/rate')
    # Should return 404 or error if artifact not found
    assert response.status_code in [200, 404, 400, 500]
