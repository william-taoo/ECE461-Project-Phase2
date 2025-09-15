# tests/test_cli_parser.py
import pytest
from pathlib import Path

from CLI_parser import build_parser, read_urls, run


def test_build_parser_accepts_url_file(tmp_path: Path):
    """build_parser should parse a single positional url_file argument."""
    f = tmp_path / "urls.txt"
    f.write_text("https://example.com\n", encoding="utf-8")

    ns = build_parser().parse_args([str(f)])
    assert ns.url_file == f


def test_read_urls_skips_blanks_and_comments(tmp_path: Path):
    """read_urls should trim whitespace and skip blank/comment lines."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "# a comment\n\n https://a\nhttps://b  \n   \n# another\n",
        encoding="utf-8",
    )
    assert read_urls(f) == ["https://a", "https://b"]


def test_read_urls_missing_file_raises(tmp_path: Path):
    """read_urls should raise FileNotFoundError if the file is missing."""
    missing = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        read_urls(missing)


def test_run_prints_urls_and_returns_zero(tmp_path: Path, capsys):
    """run() should print cleaned URLs and return 0 on success."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "# comment\nhttps://x\n https://y \n",
        encoding="utf-8",
    )
    exit_code = run([str(f)])
    captured = capsys.readouterr()
    # Expect one URL per line, in order, newline-terminated
    assert exit_code == 0
    assert captured.out.splitlines() == ["https://x", "https://y"]


def test_run_nonexistent_file_returns_one(tmp_path: Path, capsys):
    """run() should print an error and return 1 when file is missing."""
    missing = tmp_path / "nope.txt"
    exit_code = run([str(missing)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.out
