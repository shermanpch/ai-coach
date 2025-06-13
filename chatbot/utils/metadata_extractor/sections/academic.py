"""
Academic environment metadata extraction for Peterson university data.
"""

from typing import Any, Dict


def extract_academic_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract academic environment metadata fields.

    Fields extracted:
    - total_faculty: Total number of faculty members
    - student_faculty_ratio: Student to faculty ratio (converted to float)

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with academic environment metadata
    """
    metadata = {}

    faculty_info = json_record.get("faculty", {})
    metadata["total_faculty"] = faculty_info.get("total_faculty")

    # Parse student-faculty ratio
    ratio_str = faculty_info.get("student_faculty_ratio", "")
    if ratio_str and ":" in ratio_str and ratio_str != "0:1":
        try:
            student_part = ratio_str.split(":")[0]
            if student_part.isdigit():
                metadata["student_faculty_ratio"] = float(student_part)
        except (ValueError, IndexError):
            pass

    return metadata
