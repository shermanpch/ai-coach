# Test runner script for the CSE-6748 project

import os
import subprocess
import sys
import unittest
from pathlib import Path


def get_git_root():
    """Get the root directory of the git repository"""
    try:
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .strip()
            .decode("utf-8")
        )
        return Path(git_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Get the project root using git
PROJECT_ROOT = get_git_root()
if PROJECT_ROOT is None:
    print("Error: Not in a git repository or git not found")
    sys.exit(1)

# Change to project root and add to Python path
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


def run_tests(verbosity=2, pattern="test_*.py"):
    """
    Run all tests in the tests directory.

    Args:
        verbosity: Level of test output (0=quiet, 1=normal, 2=verbose)
        pattern: Pattern to match test files
    """
    # Get the tests directory relative to project root
    tests_dir = PROJECT_ROOT / "tests"

    # Discover and run tests from project root
    loader = unittest.TestLoader()
    start_dir = str(tests_dir)
    suite = loader.discover(start_dir, pattern=pattern, top_level_dir=str(PROJECT_ROOT))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Return success/failure
    return result.wasSuccessful()


def main():
    """Main entry point for the test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run tests for the CSE-6748 project")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument(
        "-p",
        "--pattern",
        default="test_*.py",
        help="Pattern to match test files (default: test_*.py)",
    )

    args = parser.parse_args()

    # Set verbosity level
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    print(f"Running tests with pattern: {args.pattern}")
    print(f"Project root: {PROJECT_ROOT}")
    print("-" * 50)

    # Run tests
    success = run_tests(verbosity=verbosity, pattern=args.pattern)

    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
