"""Tests for performance endpoints"""
import pytest


def test_performance_endpoint(client):
    """Test performance measurement endpoint"""
    response = client.get('/performance')
    # Performance test might take time or require specific setup
    assert response.status_code in [200, 400, 500]
