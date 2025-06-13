"""
Student body metadata extraction for Peterson university data.
"""

from typing import Any, Dict


def extract_student_body_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract student body mix metadata fields.

    Fields extracted:
    - percent_women: Percentage of women students (derived from admissions data)

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with student body metadata
    """
    metadata = {}

    # Gender distribution from admissions data
    admissions = json_record.get("admissions", {})
    overall_admissions = admissions.get("overall", {})
    gender_data = admissions.get("by_gender", {})

    if gender_data:
        total_applied = overall_admissions.get("applied") or 0
        female_applied = gender_data.get("female", {}).get("applied") or 0
        if total_applied and total_applied > 0:
            metadata["percent_women"] = female_applied / total_applied

    return metadata
