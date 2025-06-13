"""
Data loading and utility functions for Peterson converter.

This module handles data loading, ID generation, and university lookup functionality.
"""

import functools
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Set up project environment
PROJECT_ROOT, _ = setup_project_environment()
logger = setup_logger(__file__)


def generate_unique_id(uni_data: Dict, index: int) -> str:
    """
    Generate a unique identifier for a university based on its key attributes.

    Args:
        uni_data (Dict): The university data dictionary
        index (int): The index position in the original JSON array

    Returns:
        str: A unique identifier string
    """
    # Extract key identifying information
    university_name = uni_data.get("university_name", "Unknown")

    location_contact = uni_data.get("location_contact", {})
    address = location_contact.get("address", {})
    city = address.get("city", "")
    state = address.get("state", "")
    zip_code = address.get("zip_code", "")

    # Create a string that uniquely identifies this university
    identifier_string = f"{university_name}|{city}|{state}|{zip_code}|{index}"

    # Generate MD5 hash
    unique_id = hashlib.md5(identifier_string.encode("utf-8")).hexdigest()

    return unique_id


@functools.lru_cache(maxsize=1)
def load_peterson_data(input_file: Path) -> List[Dict]:
    """
    Load university data from the cleaned Peterson JSON file.

    This function is cached so that the file is only read and parsed once per
    process. Subsequent calls return the in-memory list.

    Args:
        input_file (Path): Path to the cleaned Peterson JSON file.

    Returns:
        List[Dict]: List of university records loaded from the JSON.
    """
    try:
        with open(input_file, encoding="utf-8") as f:
            universities = json.load(f)
        logger.info(
            f"Successfully loaded {len(universities)} universities from {input_file}"
        )
        return universities

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {input_file}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading {input_file}: {e}")
        sys.exit(1)


def lookup_university_by_id(unique_id: str, mapping_file: Path = None) -> Dict:
    """
    Look up university data by its unique identifier.

    Uses the cached load_peterson_data() to avoid re-reading the JSON on each call,
    and consults the ID mapping file to find the proper index.

    Args:
        unique_id (str): The unique identifier of the university.
        mapping_file (Path, optional): Path to the ID mapping JSON. If omitted,
            defaults to `<PROJECT_ROOT>/data/chatbot/peterson_documents/id_mapping.json`.

    Returns:
        Dict: The university data dictionary, or an empty dict if not found.
    """
    if mapping_file is None:
        mapping_file = (
            PROJECT_ROOT / "data" / "chatbot" / "peterson_documents" / "id_mapping.json"
        )

    try:
        id_mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Couldn't load ID mapping: {e}")
        return {}

    if unique_id not in id_mapping:
        logger.warning(f"Unique ID '{unique_id}' not found in mapping")
        return {}

    json_index = id_mapping[unique_id]["json_index"]
    universities = load_peterson_data(
        PROJECT_ROOT / "data" / "cleaned" / "peterson_data.json"
    )

    if 0 <= json_index < len(universities):
        return universities[json_index]
    else:
        logger.error(f"Invalid JSON index {json_index} for unique ID '{unique_id}'")
        return {}
