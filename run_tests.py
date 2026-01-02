"""Test runner script with coverage reporting.

Usage:
    python run_tests.py              # Run all tests with coverage
    python run_tests.py --fast       # Run unit tests only
    python run_tests.py --security   # Run security tests
    python run_tests.py --module core # Test specific module
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(args: argparse.Namespace) -> int:
    """Run pytest with specified options.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code from pytest
    """
    cmd = ["python", "-m", "pytest"]

    # Add markers
    if args.fast:
        cmd.extend(["-m", "unit"])
    elif args.security:
        cmd.extend(["-m", "security"])
    elif args.integration:
        cmd.extend(["-m", "integration"])

    # Add module filter
    if args.module:
        test_path = Path("tests") / args.module
        if test_path.exists():
            cmd.append(str(test_path))
        else:
            print(f"Error: Test path not found: {test_path}")
            return 1

    # Coverage options
    if not args.no_cov:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
        ])

    # Verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Additional pytest args
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)

    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests with coverage reporting"
    )

    # Test selection
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run unit tests only (fast)",
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security tests",
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests",
    )
    parser.add_argument(
        "--module",
        choices=["core", "utils", "ui"],
        help="Test specific module",
    )

    # Coverage
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Disable coverage reporting",
    )

    # Output
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    # Pass-through args
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional pytest arguments",
    )

    args = parser.parse_args()
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
