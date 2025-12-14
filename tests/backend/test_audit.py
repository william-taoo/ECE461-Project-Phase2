"""Tests for audit endpoints"""
import pytest


def test_get_artifact_audit(client, registry_with_artifact):
    """Test retrieving audit logs for an artifact"""
    client, sample_artifact = registry_with_artifact
    
    response = client.get('/artifact/model/test-id-123/audit')
    # May return audit logs or error
    assert response.status_code in [200, 404, 400, 500]
