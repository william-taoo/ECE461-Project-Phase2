"""
Tests for logging functionality.

These tests ensure the logging setup function behaves correctly:
 - Setting up logging based on LOG_LEVEL and LOG_FILE environment variables
 - Creating blank log files for silent mode (LOG_LEVEL=0)
 - Configuring proper logging levels for INFO (LOG_LEVEL=1) and DEBUG (LOG_LEVEL=2)
 - Handling invalid or missing environment variables
 - Error handling for invalid log file paths and permissions
"""

from __future__ import annotations
import pytest
import os
import sys
import logging
from pathlib import Path
from unittest.mock import patch, mock_open
from tempfile import TemporaryDirectory
import tempfile

# Import the main module to test the setup_logging function
import main


class TestLogging:
    """Test class for logging functionality."""

    def setup_method(self):
        """Reset logging configuration before each test."""
        # Clear all handlers and reset logging
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)
        logging.getLogger().propagate = True
        logging.getLogger().disabled = False
        logging.disable(logging.NOTSET)

    def test_setup_logging_silent_mode(self, tmp_path: Path) -> None:
        """Test logging setup in silent mode (LOG_LEVEL=0)."""
        log_file = tmp_path / "test.log"
        log_file.write_text("existing content", encoding="utf-8")
        
        with patch.dict(os.environ, {"LOG_LEVEL": "0", "LOG_FILE": str(log_file)}):
            main.setup_logging()
        
        # Verify log file is blank
        assert log_file.read_text(encoding="utf-8") == ""
        
        # Verify logging is disabled
        assert logging.getLogger().disabled is True
   
    def test_setup_logging_no_log_file_env(self, capsys) -> None:
        """Test logging setup when LOG_FILE environment variable is not set."""
        with patch.dict(os.environ, {"LOG_LEVEL": "1"}, clear=True):
            if "LOG_FILE" in os.environ:
                del os.environ["LOG_FILE"]
            
            with pytest.raises(SystemExit) as exc_info:
                main.setup_logging()
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Warning: LOG_FILE environment variable is not set." in captured.err

    def test_setup_logging_nonexistent_log_file(self, capsys) -> None:
        """Test logging setup with nonexistent log file path."""
        nonexistent_file = "/nonexistent/path/to/file.log"
        
        with patch.dict(os.environ, {"LOG_LEVEL": "1", "LOG_FILE": nonexistent_file}):
            with pytest.raises(SystemExit) as exc_info:
                main.setup_logging()
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert f"Error: LOG_FILE '{nonexistent_file}' does not exist or is a directory." in captured.err

    