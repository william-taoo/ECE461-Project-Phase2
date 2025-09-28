import sys
import subprocess
import json
import os

def run_tests_and_coverage():
    """
    Runs pytest silently, captures test and coverage results, and cleans up.
    Exits with 0 on success and a non-zero code on failure.
    """
    command = [
        sys.executable,
        "-m", "pytest",
        "-qq", "--tb=no",
        "--cov=.",
        "--cov-report=json:coverage.json",
        "--json-report",
        "--json-report-file=report.json",
        "tests/"
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
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


    summary_message = f"{passed_count}/{total_count} test cases passed. {coverage_percent}% line coverage achieved. "
    print(summary_message)
    
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