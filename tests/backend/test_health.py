"""Tests for health check endpoints"""
import pytest


def test_health_check(client):
    """Test basic health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'OK'


def test_health_check_components(client):
    """Test health check components endpoint"""
    response = client.get('/health/components')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert 'components' in data
    assert isinstance(data['components'], list)
    assert len(data['components']) > 0
    assert 'id' in data['components'][0]
    assert 'status' in data['components'][0]
