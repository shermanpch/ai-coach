"""
Campus housing metadata extraction for Peterson university data.
"""

from typing import Any, Dict


def extract_housing_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract campus housing metadata fields.

    Fields extracted:
    - college_owned_housing: Whether college owns housing (boolean)
    - housing_required_first_year: Whether housing is required for first year (boolean)
    - percent_students_on_campus: Percentage of students living on campus (0-1 decimal)

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with housing metadata
    """
    metadata = {}

    campus_life = json_record.get("campus_life", {})
    housing_info = campus_life.get("housing", {})

    metadata["college_owned_housing"] = housing_info.get("college_owned_housing")
    metadata["housing_required_first_year"] = housing_info.get("housing_requirements")

    # Convert percentage to 0-1 float
    percent_in_housing = housing_info.get("percent_undergrads_in_college_housing")
    if percent_in_housing is not None:
        metadata["percent_students_on_campus"] = percent_in_housing / 100.0

    return metadata
