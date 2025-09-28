"""
Tests for CustomObjects.Code.

These tests validate code-analysis helpers and the overall quality scoring:
 - counting Python lines of code in a repo tree
 - invoking flake8 and aggregating reported issues
 - handling unsupported hosts and clone failures
 - computing quality from LOC and flake8 counts

Network and filesystem operations are mocked/stubbed so tests run offline.
"""

from __future__ import annotations
from unittest.mock import MagicMock
import pytest
from typing import Any
from CustomObjects.Code import Code

def test_count_python_loc(tmp_path: pytest.TempPathFactory) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    f1 = root / "a.py"
    f1.write_text("print(1)\nprint(2)\n")
    sub = root / "sub"
    sub.mkdir()
    f2 = sub / "b.py"
    f2.write_text("x=1\n")
    c = Code(code_url="https://github.com/org/repo")
    loc = c.count_python_loc(str(root))
    assert loc == 3


def test_run_flake8_reports(monkeypatch: Any, tmp_path: pytest.TempPathFactory) -> None:
    c = Code(code_url="https://github.com/org/repo")
    class Report:
        total_errors = 5
    class Style:
        def check_files(self, paths: Any) -> Report:
            return Report()
    monkeypatch.setattr('CustomObjects.Code.flake8.get_style_guide', lambda quiet=1: Style())
    assert c.run_flake8(str(tmp_path)) == 5


def test_get_quality_no_url() -> None:
    c = Code(code_url=None)
    assert c.get_quality() == 0.0


def test_get_quality_unsupported_host() -> None:
    c = Code(code_url="https://example.com/repo")
    assert c.get_quality() == 0.0


def test_get_quality_clone_fails(monkeypatch: Any) -> None:
    c = Code(code_url="https://github.com/org/repo")
    def fake_clone(url: str, tmpdir: str, depth: int=1, single_branch: bool=True) -> RuntimeError:
        raise RuntimeError('clone failed')
    monkeypatch.setattr('CustomObjects.Code.git.Repo.clone_from', fake_clone)
    assert c.get_quality() == 0.0


def test_get_quality_no_python_files(monkeypatch: Any, tmp_path: pytest.TempPathFactory) -> None:
    # simulate clone by creating temp dir and returning a dummy repo object
    tmpdir = str(tmp_path)
    def fake_clone(url: str, td: str, depth: int=1, single_branch: bool=True) -> MagicMock:
        return MagicMock()
    monkeypatch.setattr('CustomObjects.Code.git.Repo.clone_from', fake_clone)
    # monkeypatch count_python_loc to return 0
    monkeypatch.setattr('CustomObjects.Code.Code.count_python_loc', lambda self, root: 0)
    c = Code(code_url="https://github.com/org/repo")
    assert c.get_quality() == 0.0


def test_get_quality_zero_errors(monkeypatch: Any, tmp_path: pytest.TempPathFactory) -> None:
    # simulate clone and one python file, zero flake8 errors -> quality 1.0
    def fake_clone(url: str, td: str, depth: int=1, single_branch: bool=True) -> MagicMock:
        return MagicMock()
    monkeypatch.setattr('CustomObjects.Code.git.Repo.clone_from', fake_clone)
    monkeypatch.setattr('CustomObjects.Code.Code.count_python_loc', lambda self, root: 10)
    monkeypatch.setattr('CustomObjects.Code.Code.run_flake8', lambda self, root: 0)
    c = Code(code_url="https://github.com/org/repo")
    q = c.get_quality()
    assert q == 1.0


def test_get_quality_with_errors(monkeypatch: Any, tmp_path: pytest.TempPathFactory) -> None:
    # simulate clone and python files with flake8 errors -> computed score
    def fake_clone(url, td, depth=1, single_branch=True):
        return MagicMock()
    monkeypatch.setattr('CustomObjects.Code.git.Repo.clone_from', fake_clone)
    monkeypatch.setattr('CustomObjects.Code.Code.count_python_loc', lambda self, root: 50)
    monkeypatch.setattr('CustomObjects.Code.Code.run_flake8', lambda self, root: 5)
    c = Code(code_url="https://github.com/org/repo")
    q = c.get_quality()
    # score = 1 - LOC/(error_count*5) => 1 - 50/(5*5)=1 - 2 = -1 -> clamp to 0
    assert q == 0.0
