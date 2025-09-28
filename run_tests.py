import sys
import subprocess
import json
import os

def run_tests_and_coverage():
    """
    Runs pytest, captures test and coverage results, and prints a summary.
    Exits with 0 on success and a non-zero code on failure.
    """
    command = [
        sys.executable,
        "-m", "pytest",
        "-qq", "--tb=no",
        "--cov=.",  # Automatically discover and measure all imported modules
        "--cov-report=json:coverage.json",
        "--json-report",
        "--json-report-file=report.json",
        "tests/"
    ]

    result = subprocess.run(command)
    
    passed_count = 0
    total_count = 0
    coverage_percent = 0

    try:
        with open("report.json") as f:
            report_data = json.load(f)
        summary = report_data.get("summary", {})
        passed_count = summary.get("passed", 0)
        total_count = summary.get("total", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Test report 'report.json' not found. Pytest may have failed.", file=sys.stderr)
        return result.returncode or 1

    try:
        with open("coverage.json") as f:
            coverage_data = json.load(f)
        coverage_percent = int(round(coverage_data.get("totals", {}).get("percent_covered", 0.0)))
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: Could not parse 'coverage.json'. Reporting 0% coverage.", file=sys.stderr)
        coverage_percent = 0

    # --- Print Final Output ---
    print(f"{passed_count}/{total_count} test cases passed. {coverage_percent}% line coverage achieved. ")
    
    # --- Clean up report files ---
    if os.path.exists("report.json"):
        os.remove("report.json")
    if os.path.exists("coverage.json"):
        os.remove("coverage.json")

    # Return the original exit code from pytest
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests_and_coverage()
    sys.exit(exit_code)