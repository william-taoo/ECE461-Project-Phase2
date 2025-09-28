import importlib
import logging
import os
import stat
import sys
from pathlib import Path

import pytest


def _unload_main():
    """Ensure we import a fresh copy of main each time (so top-level code re-runs)."""
    if "main" in sys.modules:
        del sys.modules["main"]


@pytest.fixture(autouse=True)
def isolate_env_and_logger(monkeypatch):
    """
    - Clear env (LOG_FILE/LOG_LEVEL/GITHUB_TOKEN) before each test.
    - Reset root logger handlers/levels to avoid cross-test contamination.
    """
    for k in ("LOG_FILE", "LOG_LEVEL", "GITHUB_TOKEN"):
        monkeypatch.delenv(k, raising=False)

    # Make sure our project root is importable
    monkeypatch.setenv("PYTHONPATH", str(Path.cwd()))

    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    for h in old_handlers:
        root.removeHandler(h)
    root.handlers.clear()
    logging.disable(logging.NOTSET)

    yield

    # Restore logger state
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in old_handlers:
        root.addHandler(h)
    root.setLevel(old_level)
    logging.disable(logging.NOTSET)

    # Unload main so later tests can re-import cleanly
    _unload_main()


def import_main_expect_exit_code(expected_code: int):
    """
    Import main and assert that its top-level setup_logging() causes SystemExit(expected_code).
    """
    _unload_main()
    with pytest.raises(SystemExit) as ei:
        importlib.import_module("main")
    assert int(ei.value.code) == int(expected_code)


def import_main_expect_success():
    """
    Import main and expect it to succeed (no SystemExit). Return the imported module.
    """
    _unload_main()
    return importlib.import_module("main")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text()


# ---------------------------
# Tests for setup_logging()
# ---------------------------

def test_unset_log_file_exits_1(monkeypatch):
    """
    LOG_FILE unset -> program should exit 1 on import (top-level setup_logging()).
    """
    monkeypatch.setenv("LOG_LEVEL", "1")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    import_main_expect_exit_code(1)


def test_invalid_path_exits_1(tmp_path, monkeypatch):
    """
    LOG_FILE points to a path that does NOT exist -> exit 1.
    (Matches the autograder's 'Invalid Log File Path' test.)
    """
    lf = tmp_path / "nope" / "ece461.log"  # parent doesn't exist
    monkeypatch.setenv("LOG_LEVEL", "1")
    monkeypatch.setenv("LOG_FILE", str(lf))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    import_main_expect_exit_code(1)


def test_directory_as_log_file_exits_1(tmp_path, monkeypatch):
    """
    LOG_FILE is a directory -> exit 1.
    """
    monkeypatch.setenv("LOG_LEVEL", "1")
    monkeypatch.setenv("LOG_FILE", str(tmp_path))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    import_main_expect_exit_code(1)


def test_level0_truncates_existing_file(tmp_path, monkeypatch):
    """
    LOG_LEVEL=0: disable logging and truncate file to 0 bytes; import succeeds.
    """
    lf = tmp_path / "level0.log"
    lf.write_text("PREEXISTING", encoding="utf-8")
    monkeypatch.setenv("LOG_LEVEL", "0")
    monkeypatch.setenv("LOG_FILE", str(lf))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    m = import_main_expect_success()
    assert lf.exists()
    assert lf.stat().st_size == 0

    logging.getLogger().handlers.clear()
    importlib.reload(m)


def test_level1_info_only(tmp_path, monkeypatch):
    """
    LOG_LEVEL=1: should log INFO 'program_start' but not 'debug_enabled'.
    """
    lf = tmp_path / "level1.log"
    lf.touch()
    monkeypatch.setenv("LOG_LEVEL", "1")
    monkeypatch.setenv("LOG_FILE", str(lf))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    m = import_main_expect_success()
    s = read_text(lf)
    assert "program_start" in s
    assert "debug_enabled" not in s

    logging.getLogger().handlers.clear()
    importlib.reload(m)


def test_level2_info_and_debug(tmp_path, monkeypatch):
    """
    LOG_LEVEL=2: should log both 'program_start' and 'debug_enabled'.
    """
    lf = tmp_path / "level2.log"
    lf.touch()
    monkeypatch.setenv("LOG_LEVEL", "2")
    monkeypatch.setenv("LOG_FILE", str(lf))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    m = import_main_expect_success()
    s = read_text(lf)
    assert "program_start" in s
    assert "debug_enabled" in s

    logging.getLogger().handlers.clear()
    importlib.reload(m)


def test_invalid_log_level_defaults_to_0(tmp_path, monkeypatch):
    """
    Invalid LOG_LEVEL -> default to 0: file is truncated, import succeeds.
    """
    lf = tmp_path / "invalid_level.log"
    lf.write_text("PREEXISTING", encoding="utf-8")
    monkeypatch.setenv("LOG_LEVEL", "garbage")
    monkeypatch.setenv("LOG_FILE", str(lf))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    m = import_main_expect_success()
    assert lf.stat().st_size == 0

    logging.getLogger().handlers.clear()
    importlib.reload(m)


def test_non_writable_file_exits_1(tmp_path, monkeypatch):
    """
    Make LOG_FILE read-only, then require logging at level 1.
    Opening the FileHandler should fail -> exit 1.

    Note: On some Windows setups, read-only may still allow appends depending on ACLs.
    In that rare case, we explicitly fail so we notice it rather than silently skipping.
    """
    lf = tmp_path / "readonly.log"
    lf.touch()

    # Make file read-only (works on POSIX; on Windows sets the read-only attribute)
    try:
        os.chmod(lf, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        # Fallback: ensure at least user read-only
        os.chmod(lf, stat.S_IREAD)

    monkeypatch.setenv("LOG_LEVEL", "1")
    monkeypatch.setenv("LOG_FILE", str(lf))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    try:
        import_main_expect_exit_code(1)
    finally:
        # Restore write so pytest can clean tmp files
        try:
            os.chmod(lf, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass
