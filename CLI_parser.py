# CLI_Parser.py

import argparse
from pathlib import Path
import sys
from typing import List, Tuple, Optional


def build_parser() -> argparse.ArgumentParser:
    """
    Builds the argument parser for the CLI.

    Returns:
        An argparse.ArgumentParser instance.
    """
    p = argparse.ArgumentParser(
        prog="trustworthy-cli",
        description=(
            "Read a URL file and process the model, code, and dataset URLs."
        )
    )
    p.add_argument("url_file", type=Path, help="Path to a text file containing URLs.")
    return p


def parse_input_file(path: Path) -> List[Tuple[Optional[str], Optional[str], str]]:
    """
    Parses the URL file, handling blank fields and shared datasets.

    Returns:
        A list of tuples, where each tuple is (code_url, dataset_url, model_url).
    """
    parsed_data = []
    last_seen_dataset: Optional[str] = None

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or not "," in line:
                continue # Skip empty or non-csv lines

            parts = [p.strip() for p in line.split(",")]

            # Exit code if more than 3 urls are found in a line
            if len(parts) > 3:
                print(f"Too many fields in line: {line}", file=sys.stderr)
                sys.exit(1)
            
            # Ensure we always have 3 parts to unpack
            while len(parts) < 3:
                parts.append("")

            code_url, dataset_url, model_url = parts

            # Rule: A model URL is required.
            if not model_url:
                continue

            # Rule: If a dataset is provided, it becomes the new "last seen"
            if dataset_url:
                last_seen_dataset = dataset_url
            # Rule: If no dataset is provided, use the last one we saw
            else:
                dataset_url = last_seen_dataset

            # Store the final tuple for this model. Use None for empty strings.
            parsed_data.append((
                code_url if code_url else None,
                dataset_url if dataset_url else None,
                model_url
            ))

    return parsed_data

