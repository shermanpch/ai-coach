import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

load_dotenv()

# US State abbreviation to full name mapping
STATE_MAPPING = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
    "PR": "Puerto Rico",
    "VI": "Virgin Islands",
    "AS": "American Samoa",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
}

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def clean_malformed_entries(data: Any, university_name: str = "Unknown") -> Any:
    """
    Recursively clean malformed entries from the data structure.

    Args:
        data: The data structure to clean
        university_name: Name of the university for logging purposes

    Returns:
        Cleaned data structure
    """
    if isinstance(data, dict):
        cleaned_dict = {}
        for key, value in data.items():
            cleaned_dict[key] = clean_malformed_entries(value, university_name)
        return cleaned_dict

    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            # Check for malformed string entries that look like broken JSON
            if isinstance(item, str):
                # Detect malformed patterns like "test_scores_accepted:[{"
                if any(
                    pattern in item
                    for pattern in [
                        "test_scores_accepted:[{",
                        ":[{",
                        ":]}",
                        '":[{',
                        '":]}',
                    ]
                ):
                    logger.warning(
                        f"Removing malformed string entry from {university_name}: {item}"
                    )
                    continue  # Skip this malformed entry
                else:
                    # Keep valid string entries
                    cleaned_list.append(item)
            else:
                # Recursively clean non-string items
                cleaned_list.append(clean_malformed_entries(item, university_name))
        return cleaned_list

    else:
        # Return primitive types as-is
        return data


def clean_requirements_section(university_data: Dict) -> Dict:
    """
    Specifically clean the requirements section of malformed entries.

    Args:
        university_data: Dictionary containing university data

    Returns:
        Cleaned university data
    """
    university_name = university_data.get("university_name", "N/A")

    # Navigate to the requirements section
    admissions = university_data.get("admissions", {})
    requirements = admissions.get("requirements", [])

    if requirements:
        original_length = len(requirements)
        cleaned_requirements = []

        for req in requirements:
            # Keep only dictionary entries, remove malformed strings
            if isinstance(req, dict):
                # Also clean the dictionary recursively
                cleaned_req = clean_malformed_entries(req, university_name)
                cleaned_requirements.append(cleaned_req)
            elif isinstance(req, str):
                logger.warning(
                    f"Removing malformed requirement string from {university_name}: {req}"
                )
            else:
                logger.warning(
                    f"Removing unexpected requirement type from {university_name}: {type(req)} - {req}"
                )

        admissions["requirements"] = cleaned_requirements

        if len(cleaned_requirements) != original_length:
            logger.info(
                f"Cleaned requirements for {university_name}: {original_length} -> {len(cleaned_requirements)} entries"
            )

    return university_data


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
            # Clean the extracted data
            university_name = extracted_json.get(
                "university_name", f"Unknown from {json_file.name}"
            )

            # Apply comprehensive cleaning
            cleaned_data = clean_malformed_entries(extracted_json, university_name)
            cleaned_data = clean_requirements_section(cleaned_data)
            cleaned_data = convert_state_abbreviation(cleaned_data)

            extracted_data.append(cleaned_data)
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


def convert_state_abbreviation(university_data: Dict) -> Dict:
    """
    Convert state abbreviation to full state name in location_contact.

    Args:
        university_data: Dictionary containing university data

    Returns:
        University data with full state name
    """
    university_name = university_data.get("university_name", "N/A")

    # Navigate to the location_contact section
    location_contact = university_data.get("location_contact", {})
    address = location_contact.get("address", {})

    if "state" in address:
        state_abbrev = address["state"]

        # Convert abbreviation to full name if mapping exists
        if state_abbrev in STATE_MAPPING:
            full_state_name = STATE_MAPPING[state_abbrev]
            address["state"] = full_state_name
            logger.info(
                f"Converted state for {university_name}: {state_abbrev} -> {full_state_name}"
            )
        else:
            logger.warning(
                f"No mapping found for state abbreviation '{state_abbrev}' in {university_name}"
            )

    return university_data


def main():
    """Main function to orchestrate the Peterson data cleaning process"""
    logger.info("Peterson Data Cleaner - Starting...")

    process_peterson_data()

    logger.info("Peterson Data Cleaner - Complete!")


if __name__ == "__main__":
    main()
