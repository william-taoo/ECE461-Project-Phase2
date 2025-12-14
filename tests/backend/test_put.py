"""Tests for artifact update endpoints"""
import pytest
import json


def test_update_artifact_success(client, registry_with_artifact):
    """Test updating an artifact that exists"""
    client, sample_artifact = registry_with_artifact
    
    update_data = {
        "url": "https://example.com/updated-model"
    }
    
    response = client.put('/artifacts/model/test-id-123', json=update_data)
    assert response.status_code == 200


def test_update_artifact_not_found(client):
    """Test updating an artifact that doesn't exist"""
    update_data = {"url": "https://example.com/model"}
    response = client.put('/artifacts/model/nonexistent-id', json=update_data)
    assert response.status_code == 404


def test_update_artifact_no_data(client, registry_with_artifact):
    """Test updating artifact without data"""
    client, sample_artifact = registry_with_artifact
    
    # PUT request without JSON data should fail
    response = client.put('/artifacts/model/test-id-123', headers={'Content-Type': 'application/json'})
    assert response.status_code in [400, 415, 500]
