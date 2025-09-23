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


def test_read_urls_skips_blanks_and_whitespace(tmp_path: Path):
    """read_urls should trim whitespace and skip blank lines."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "\n  https://a \nhttps://b  \n   \n",
        encoding="utf-8",
    )
    assert read_urls(f) == ["https://a", "https://b"]


def test_read_urls_parses_csv_triple_in_order(tmp_path: Path):
    """CSV lines should be parsed as <code>, <dataset>, <model> and emitted in that order."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "https://github.com/google-research/bert, https://huggingface.co/datasets/bookcorpus/bookcorpus, https://huggingface.co/google-bert/bert-base-uncased\n",
        encoding="utf-8",
    )
    urls = read_urls(f)
    assert urls == [
        "https://github.com/google-research/bert",
        "https://huggingface.co/datasets/bookcorpus/bookcorpus",
        "https://huggingface.co/google-bert/bert-base-uncased",
    ]


def test_read_urls_csv_with_missing_fields(tmp_path: Path):
    """
    CSV rows may have blank code/dataset.
    If model is blank, the row is effectively skipped for the model, but non-empty fields are still emitted.
    """
    f = tmp_path / "urls.txt"
    f.write_text(
        # only model present
        ",,https://huggingface.co/parvk11/audience_classifier_model\n"
        # code + model present, dataset blank
        "https://github.com/org/repo, , https://huggingface.co/org/model\n"
        # code + dataset present, model blank -> only code and dataset emitted
        "https://github.com/only/code, https://huggingface.co/datasets/x/y, \n",
        encoding="utf-8",
    )
    urls = read_urls(f)
    assert urls == [
        "https://huggingface.co/parvk11/audience_classifier_model",
        "https://github.com/org/repo",
        "https://huggingface.co/org/model",
        "https://github.com/only/code",
        "https://huggingface.co/datasets/x/y",
    ]


def test_read_urls_missing_file_raises(tmp_path: Path):
    """read_urls should raise FileNotFoundError if the file is missing."""
    missing = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        read_urls(missing)


def test_run_prints_urls_and_returns_zero(tmp_path: Path, capsys):
    """run() should print cleaned URLs and return 0 on success."""
    f = tmp_path / "urls.txt"
    f.write_text(
        # one CSV triple plus single-line URLs and blanks
        "https://github.com/google-research/bert, https://huggingface.co/datasets/bookcorpus/bookcorpus, https://huggingface.co/google-bert/bert-base-uncased\n"
        "\n"
        " https://extra-single\n",
        encoding="utf-8",
    )
    exit_code = run([str(f)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.splitlines() == [
        "https://github.com/google-research/bert",
        "https://huggingface.co/datasets/bookcorpus/bookcorpus",
        "https://huggingface.co/google-bert/bert-base-uncased",
        "https://extra-single",
    ]


def test_run_nonexistent_file_returns_one(tmp_path: Path, capsys):
    """run() should print an error (to stderr) and return 1 when file is missing."""
    missing = tmp_path / "nope.txt"
    exit_code = run([str(missing)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.err
