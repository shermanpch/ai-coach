#!/usr/bin/env python3
"""
Script to combine Peterson course data with Peterson university data.
This script loads JSON files from peterson_courses_data and replaces the
majors_and_degrees key in corresponding files in peterson_data.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


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

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging
script_name = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"{script_name}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Change to project root
os.chdir(PROJECT_ROOT)


def load_json_file(file_path: Path) -> Dict[Any, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}


def save_json_file(file_path: Path, data: Dict[Any, Any]) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        return False


def extract_filename_from_path(file_path: Path) -> str:
    """Extract the filename without extension from a Path object."""
    return file_path.stem


def main():
    """Main function to combine Peterson course data with university data."""
    logger.info("Starting Peterson course data combination...")

    # Define the directories
    courses_data_dir = PROJECT_ROOT / "data" / "external" / "peterson_courses_data"
    peterson_data_dir = PROJECT_ROOT / "data" / "external" / "peterson_data"

    logger.info(f"Courses data directory: {courses_data_dir}")
    logger.info(f"Peterson data directory: {peterson_data_dir}")

    # Check if directories exist
    if not courses_data_dir.exists():
        logger.error(f"Courses data directory not found: {courses_data_dir}")
        sys.exit(1)

    if not peterson_data_dir.exists():
        logger.error(f"Peterson data directory not found: {peterson_data_dir}")
        sys.exit(1)

    # Get all JSON files from courses data directory
    courses_files = list(courses_data_dir.glob("*.json"))
    logger.info(f"Found {len(courses_files)} course data files")

    # Get all JSON files from peterson data directory
    peterson_files = list(peterson_data_dir.glob("*.json"))
    logger.info(f"Found {len(peterson_files)} peterson data files")

    # Create a mapping of filename to full path for peterson data files
    peterson_file_map = {}
    for file_path in peterson_files:
        filename = extract_filename_from_path(file_path)
        peterson_file_map[filename] = file_path

    updated_count = 0
    not_found_count = 0
    error_count = 0

    # Process each course data file
    for courses_file in courses_files:
        filename = extract_filename_from_path(courses_file)
        logger.debug(f"Processing: {filename}")

        # Check if corresponding peterson data file exists
        if filename not in peterson_file_map:
            logger.warning(f"No corresponding peterson data file found for {filename}")
            not_found_count += 1
            continue

        # Load the course data
        courses_data = load_json_file(courses_file)
        if not courses_data:
            logger.error(f"Could not load courses data from {courses_file}")
            error_count += 1
            continue

        # Load the peterson data
        peterson_file_path = peterson_file_map[filename]
        peterson_data = load_json_file(peterson_file_path)
        if not peterson_data:
            logger.error(f"Could not load peterson data from {peterson_file_path}")
            error_count += 1
            continue

        # Check if majors_and_degrees exists in courses data
        if (
            "json" not in courses_data
            or "majors_and_degrees" not in courses_data["json"]
        ):
            logger.warning(
                f"No majors_and_degrees found in courses data for {filename}"
            )
            not_found_count += 1
            continue

        # Check if peterson data has the expected structure
        if "json" not in peterson_data:
            logger.error(
                f"Peterson data does not have expected 'json' structure for {filename}"
            )
            error_count += 1
            continue

        # Replace the majors_and_degrees in peterson data
        old_majors = peterson_data["json"].get("majors_and_degrees", [])
        new_majors = courses_data["json"]["majors_and_degrees"]

        peterson_data["json"]["majors_and_degrees"] = new_majors

        # Save the updated peterson data
        if save_json_file(peterson_file_path, peterson_data):
            logger.debug(f"Updated majors_and_degrees for {filename}")
            logger.debug(
                f"  Old: {len(old_majors) if isinstance(old_majors, list) else 'N/A'} categories"
            )
            logger.debug(
                f"  New: {len(new_majors) if isinstance(new_majors, list) else 'N/A'} categories"
            )
            updated_count += 1
        else:
            logger.error(f"Could not save updated data for {filename}")
            error_count += 1

    # Print summary
    logger.info("=" * 50)
    logger.info("SUMMARY:")
    logger.info(f"Total course files processed: {len(courses_files)}")
    logger.info(f"Successfully updated: {updated_count}")
    logger.info(f"Not found in peterson data: {not_found_count}")
    logger.info(f"Errors encountered: {error_count}")
    logger.info("=" * 50)

    if error_count > 0:
        logger.error(f"Script completed with {error_count} errors")
        sys.exit(1)
    else:
        logger.info("Script completed successfully!")


if __name__ == "__main__":
    main()
