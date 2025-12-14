"""Tests for artifact by name endpoint"""
import pytest


def test_artifact_by_name_found(client, registry_with_artifact):
    """Test retrieving artifact by name when it exists"""
    client, sample_artifact = registry_with_artifact
    
    response = client.get('/artifact/byName/test-model')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['name'] == 'test-model'


def test_artifact_by_name_not_found(client):
    """Test retrieving artifact by name when it doesn't exist"""
    response = client.get('/artifact/byName/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
