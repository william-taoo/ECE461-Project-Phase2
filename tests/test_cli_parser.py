"""
Tests for CLI_parser.

These tests ensure the command-line parser and helper functions behave as expected:
 - parsing the single positional url_file argument
 - trimming whitespace and skipping blank/invalid lines
 - handling CSV triples and carrying forward the last seen dataset URL
 - error behaviour when files are missing
"""

from __future__ import annotations
import pytest
from pathlib import Path

# Import the new function
from CLI_parser import build_parser, parse_input_file

def test_build_parser_accepts_url_file(tmp_path: Path) -> None:
    """build_parser should parse a single positional url_file argument."""
    f = tmp_path / "urls.txt"
    f.write_text("https://example.com\n", encoding="utf-8")

    ns = build_parser().parse_args([str(f)])
    assert ns.url_file == f

def test_parse_input_file_skips_blanks_and_whitespace(tmp_path: Path) -> None:
    """parse_input_file should skip blank lines and lines with only whitespace."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "\n   \n  https://a.com,,https://model.com\n \n",
        encoding="utf-8",
    )
    # It should only parse the one valid line
    assert len(parse_input_file(f)) == 1

def test_parse_input_file_parses_csv_triple(tmp_path: Path) -> None:
    """CSV lines should be parsed as a tuple of (code, dataset, model)."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "https://github.com/a/b, https://huggingface.co/datasets/c/d, https://huggingface.co/e/f\n",
        encoding="utf-8",
    )
    result = parse_input_file(f)
    assert result == [
        ("https://github.com/a/b", "https://huggingface.co/datasets/c/d", "https://huggingface.co/e/f")
    ]

def test_parse_input_file_handles_missing_fields_as_none(tmp_path: Path) -> None:
    """Blank fields for code or dataset in a CSV row should become None."""
    f = tmp_path / "urls.txt"
    f.write_text(
        # only model present
        ",,https://model1\n"
        # code + model present, dataset blank
        "https://code2, , https://model2\n",
        encoding="utf-8",
    )
    result = parse_input_file(f)
    assert result == [
        (None, None, "https://model1"),
        ("https://code2", None, "https://model2"),
    ]

def test_parse_input_file_skips_row_if_model_url_is_missing(tmp_path: Path) -> None:
    """If a CSV row has no model URL, the entire row should be skipped."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "https://code.com, https://dataset.com, \n", # No model URL
        encoding="utf-8",
    )
    result = parse_input_file(f)
    assert result == []

def test_parse_input_file_handles_shared_dataset(tmp_path: Path) -> None:
    """If a row has no dataset URL, it should inherit the last one seen."""
    f = tmp_path / "urls.txt"
    f.write_text(
        "https://code1,https://dataset1,https://model1\n"  # This dataset should be remembered
        ",,https://model2\n"                             # This model should get dataset1
        "https://code3,,https://model3\n"                 # This model should also get dataset1
        ",https://dataset2,https://model4\n"              # A new dataset is introduced
        ",,https://model5\n",                             # This model should get dataset2
        encoding="utf-8",
    )
    result = parse_input_file(f)
    assert result == [
        ("https://code1", "https://dataset1", "https://model1"),
        (None, "https://dataset1", "https://model2"),
        ("https://code3", "https://dataset1", "https://model3"),
        (None, "https://dataset2", "https://model4"),
        (None, "https://dataset2", "https://model5"),
    ]

def test_parse_input_file_missing_file_raises(tmp_path: Path) -> None:
    """parse_input_file should raise FileNotFoundError if the file is missing."""
    missing = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        parse_input_file(missing)