#!/usr/bin/env python3
"""
Test execution script
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> bool:
    """Executes command and returns success status"""
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def check_dependencies() -> bool:
    """Checks basic dependencies"""
    required = ["pytest", "pytest-cov"]

    for package in required:
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {package.replace('-', '_')}"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            print(f"{package} not found")
            return False

    print("Dependencies OK")
    return True


def run_tests(test_type: str = "all", coverage: bool = False) -> bool:
    """Runs the tests"""
    if not check_dependencies():
        print("Install dependencies: pip install pytest pytest-cov")
        return False

    # Determine test paths
    test_paths = {
        "unit": "tests/unit/",
        "integration": "tests/integration/",
        "all": "tests/",
    }

    path = test_paths.get(test_type, "tests/")

    # Build command
    cmd = [sys.executable, "-m", "pytest", path, "-v"]

    if coverage:
        cmd.extend(
            ["--cov=app", "--cov-report=term-missing", "--cov-report=html:htmlcov"]
        )

    print(f"Running {test_type} tests...")
    return run_command(cmd)


def main():
    parser = argparse.ArgumentParser(description="Run tests")
    parser.add_argument("--unit", action="store_true", help="Unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Integration tests only"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )

    args = parser.parse_args()

    # Determine test type
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    else:
        test_type = "all"

    # Run tests
    success = run_tests(test_type, args.coverage)

    if success:
        print("Tests completed successfully!")
        if args.coverage:
            print(" Coverage report: htmlcov/index.html")
    else:
        print("Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
