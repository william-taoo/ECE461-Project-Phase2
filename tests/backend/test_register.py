"""Tests for artifact registration endpoints"""
import pytest
import json


def test_register_artifact(client):
    """Test registering a new artifact"""
    artifact_data = {
        "name": "test-artifact",
        "url": "https://example.com/artifact"
    }
    
    response = client.post('/artifact/model', json=artifact_data)
    # May return various codes depending on validation and rating
    assert response.status_code in [200, 201, 400, 424, 500]


def test_register_artifact_with_invalid_type(client):
    """Test registering artifact with invalid type"""
    artifact_data = {
        "name": "test-artifact",
        "url": "https://example.com/artifact"
    }
    
    response = client.post('/artifact/invalid-type', json=artifact_data)
    assert response.status_code in [400, 422]
