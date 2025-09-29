"""
Tests for GitHub token validation functionality.

These tests ensure the validate_github_token function behaves correctly:
 - Validating GitHub tokens via API calls
 - Handling valid and invalid tokens
 - Managing network errors and timeouts
 - Proper error handling and exit codes
 - Behavior when no token is provided
"""

from __future__ import annotations
import pytest
import os
import sys
from unittest.mock import patch, Mock
import requests

# Import the main module to test the validate_github_token function
import main


class TestGitHubTokenValidation:
    """Test class for GitHub token validation functionality."""

    @patch('requests.get')
    def test_validate_github_token_valid_token(self, mock_get: Mock) -> None:
        """Test validate_github_token with a valid token (200 response)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "valid_token_123"}):
            # Should not raise any exception or exit
            main.validate_github_token()
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once_with(
            'https://api.github.com/user',
            headers={
                'Authorization': 'token valid_token_123',
                'Accept': 'application/vnd.github.v3+json',
            },
            timeout=5
        )

    @patch('requests.get')
    def test_validate_github_token_invalid_token_401(self, mock_get: Mock, capsys) -> None:
        """Test validate_github_token with invalid token (401 response)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "invalid_token_123"}):
            with pytest.raises(SystemExit) as exc_info:
                main.validate_github_token()
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Error: GITHUB_TOKEN appears to be invalid (401 Unauthorized)" in captured.err