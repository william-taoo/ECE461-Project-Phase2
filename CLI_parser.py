import argparse
from pathlib import Path
import sys

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trustworthy-cli",
        description=(
            "Read a URL file where each line is either a single URL "
            "or a CSV triple: <code_url>, <dataset_url>, <model_url>. "
            "Prints a flat list of URLs to stdout."
        )
    )
    p.add_argument("url_file", type=Path, help="Path to a text file containing URLs.")
    return p

def read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if "," in line:
                parts = [p.strip() for p in line.split(",", 2)]
                while len(parts) < 3:
                    parts.append("")
                code, dataset, model = parts
                if code:
                    urls.append(code)
                if dataset:
                    urls.append(dataset)
                if model:
                    urls.append(model)
                else:
                    # Optional: warn about skipped row
                    # print("Warning: row missing model URL; skipping.", file=sys.stderr)
                    pass
            else:
                urls.append(line)
    return urls

def run(argv: list[str] | None = None) -> int:
    try:
        ns = build_parser().parse_args(argv)
        for url in read_urls(ns.url_file):
            sys.stdout.write(url + "\n")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(run())
