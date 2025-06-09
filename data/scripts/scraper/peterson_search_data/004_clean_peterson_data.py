import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "peterson_data_cleaner.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Change to project root
os.chdir(PROJECT_ROOT)


def load_peterson_json_file(file_path: Path) -> Dict:
    """Load and extract the json key from a Peterson data file"""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Extract the json key if it exists
        if "json" in data:
            return data["json"]
        else:
            logger.warning(f"No 'json' key found in {file_path.name}")
            return None

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path.name}: {e}")
        return None


def process_peterson_data():
    """Process all Peterson data JSON files and combine their json keys"""
    logger.info("Starting Peterson data cleaning...")

    # Define the Peterson data directory
    peterson_data_dir = PROJECT_ROOT / "data" / "external" / "peterson_data"

    if not peterson_data_dir.exists():
        logger.error(f"Peterson data directory not found: {peterson_data_dir}")
        sys.exit(1)

    # Find all JSON files in the Peterson data directory
    json_files = list(peterson_data_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files to process")

    if not json_files:
        logger.warning("No JSON files found in Peterson data directory")
        return

    # Process each file and extract the json key
    extracted_data = []
    successful_files = 0
    failed_files = 0

    for json_file in json_files:
        logger.info(f"Processing {json_file.name}")

        extracted_json = load_peterson_json_file(json_file)

        if extracted_json is not None:
            extracted_data.append(extracted_json)
            successful_files += 1
        else:
            failed_files += 1

    logger.info(
        f"Processing complete: {successful_files} successful, {failed_files} failed"
    )

    # Create output directory if it doesn't exist
    output_dir = PROJECT_ROOT / "data" / "cleaned"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the combined data
    output_file = output_dir / "peterson_data.json"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Successfully saved {len(extracted_data)} records to {output_file}"
        )

        # Log summary statistics
        logger.info("Summary:")
        logger.info(f"  Total JSON files found: {len(json_files)}")
        logger.info(f"  Successfully processed: {successful_files}")
        logger.info(f"  Failed to process: {failed_files}")
        logger.info(f"  Records in output: {len(extracted_data)}")
        logger.info(f"  Output file: {output_file}")

    except Exception as e:
        logger.error(f"Failed to save output file: {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate the Peterson data cleaning process"""
    logger.info("Peterson Data Cleaner - Starting...")

    process_peterson_data()

    logger.info("Peterson Data Cleaner - Complete!")


if __name__ == "__main__":
    main()
