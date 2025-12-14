"""Tests for artifact removal/deletion endpoints"""
import pytest
import json


def test_delete_artifact_success(client, registry_with_artifact):
    """Test deleting an artifact that exists"""
    client, sample_artifact = registry_with_artifact
    
    response = client.delete('/artifacts/model/test-id-123')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data


def test_delete_artifact_not_found(client):
    """Test deleting an artifact that doesn't exist"""
    response = client.delete('/artifacts/model/nonexistent-id')
    assert response.status_code == 404


def test_delete_artifact_invalid_type(client):
    """Test deleting with invalid artifact type"""
    response = client.delete('/artifacts/invalid-type/some-id')
    assert response.status_code == 400


def test_reset_registry(client, registry_with_artifact):
    """Test resetting the registry"""
    client, sample_artifact = registry_with_artifact
    
    response = client.delete('/reset')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
