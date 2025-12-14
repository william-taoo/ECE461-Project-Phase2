"""Tests for artifact retrieval endpoints"""
import pytest
import json


def test_get_artifacts_with_query(client, registry_with_artifact):
    """Test retrieving artifacts with a query"""
    client, sample_artifact = registry_with_artifact
    
    query = {"name": "test-model"}
    response = client.post('/artifacts', json=query)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['name'] == 'test-model'


def test_get_artifacts_missing_name(client):
    """Test retrieving artifacts without name field"""
    response = client.post('/artifacts', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
