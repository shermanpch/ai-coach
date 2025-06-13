"""
Data formatting and value processing utilities for Peterson converter.

This module contains utility functions for safely extracting and formatting
data from the Peterson university dataset.
"""

import re
from typing import Dict


def slugify(text: str) -> str:
    """
    Convert a string (university name) to a URL-friendly slug.

    Args:
        text (str): The text to slugify

    Returns:
        str: The slugified string (e.g., "Swarthmore College" -> "swarthmore-college")
    """
    if not text or text == "Not Reported":
        return "unknown"

    # Convert to lowercase
    text = text.lower()
    # Replace spaces and non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")

    return text


def get_value(data: Dict, key: str, default: str = "Not Reported") -> str:
    """
    Safely retrieve a value from a dictionary with proper formatting.

    Args:
        data (Dict): The dictionary to retrieve from
        key (str): The key to look for
        default (str): The default value if key not found or value is None/empty

    Returns:
        str: The formatted value
    """
    if not isinstance(data, dict):
        return default

    value = data.get(key)

    # Handle None or empty string
    if value is None or value == "":
        return default

    # Handle boolean values
    if isinstance(value, bool):
        return "Yes" if value else "No"

    # Handle numeric values that might be strings like "True"/"False"
    if isinstance(value, str):
        if value.lower() in ["true", "yes", "y"]:
            return "Yes"
        elif value.lower() in ["false", "no", "n"]:
            return "No"
        elif value.strip() == "":
            return default

    # Handle lists
    if isinstance(value, list):
        if not value:  # Empty list
            return default
        # Join string lists with commas
        if all(isinstance(item, str) for item in value):
            return ", ".join(value)
        else:
            # Handle mixed types in lists
            str_items = [str(item) for item in value if item is not None]
            return ", ".join(str_items) if str_items else default

    # Handle numeric values
    if isinstance(value, (int, float)):
        return str(value)

    # Return the value as string, handling any remaining edge cases
    try:
        return str(value).strip()
    except Exception:
        return default


def format_sport(sport_obj: Dict) -> str:
    """Format a sport object into a markdown line."""
    sport_name = get_value(sport_obj, "sport")
    intercollegiate = get_value(sport_obj, "intercollegiate")
    scholarship = get_value(sport_obj, "scholarship")
    intramural = get_value(sport_obj, "intramural")

    # Handle special cases for intercollegiate field that might contain division info
    if intercollegiate not in ["Yes", "No", "Not Reported"]:
        # If it contains division info like "Division 3", keep it as is
        intercollegiate_display = intercollegiate
    else:
        intercollegiate_display = intercollegiate

    return f"- **{sport_name}:** Intercollegiate: {intercollegiate_display}, Scholarship: {scholarship}, Intramural: {intramural}"
