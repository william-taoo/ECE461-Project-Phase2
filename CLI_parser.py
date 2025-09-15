import argparse
from pathlib import Path
import sys

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trustworthy-cli",
        description="Read a file of URLs (one per line) and print them to stdout."
    )
    p.add_argument("url_file", type=Path, help="Path to a text file containing URLs.")
    return p

# Given a Path to a file, open it and return a list of cleaned URLs.
def read_urls(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"URL file not found: {path}")

    urls: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            # Ignore blank lines and comments
            continue
        urls.append(s)
    return urls

# Main entry point for the CLI (used in testing)
def run(argv: list[str] | None = None) -> int:
    try:
        ns = build_parser().parse_args(argv)  # parse CLI args into namespace object
        for url in read_urls(ns.url_file):
            sys.stdout.write(url + "\n")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(run())
