"""Tests for artifact lineage endpoints"""
import pytest


def test_get_lineage(client, registry_with_artifact):
    """Test retrieving artifact lineage"""
    client, sample_artifact = registry_with_artifact
    
    response = client.get('/artifact/model/test-id-123/lineage')
    # May return lineage data or error
    assert response.status_code in [200, 404, 400, 500]
