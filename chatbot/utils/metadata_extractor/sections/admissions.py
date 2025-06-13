"""
Admissions metadata extraction for Peterson university data.
"""

from typing import Any, Dict


def extract_admissions_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract admissions and selectivity metadata fields.

    Fields extracted:
    - accept_rate: Acceptance rate (converted to 0-1 decimal)
    - avg_high_school_gpa: Average high school GPA
    - application_fee: Application fee amount
    - application_deadline_regular: Regular admission deadline
    - application_deadline_early: Early admission deadline
    - SAT verbal/math 25/75/avg: SAT score bands
    - ACT composite 25/75/avg: ACT score bands

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with admissions metadata
    """
    metadata = {}

    admissions = json_record.get("admissions", {})

    # Acceptance rate (convert percentage to 0-1 float)
    overall_admissions = admissions.get("overall", {})
    accept_rate = overall_admissions.get("acceptance_rate")
    if accept_rate is not None:
        metadata["accept_rate"] = accept_rate / 100.0  # Convert percentage to decimal

    # Application info
    applying_info = admissions.get("applying", {})
    metadata["avg_high_school_gpa"] = applying_info.get("avg_high_school_gpa")
    metadata["application_fee"] = applying_info.get("application_fee")

    # Application deadlines - extract from application_deadlines array
    deadlines = admissions.get("application_deadlines", [])
    for deadline in deadlines:
        deadline_type = deadline.get("type", "").lower()
        closing_date = deadline.get("application_closing")
        if "fall freshmen" in deadline_type and closing_date:
            metadata["application_deadline_regular"] = closing_date
        elif "early" in deadline_type and closing_date:
            metadata["application_deadline_early"] = closing_date

    # Standardized test scores
    test_scores = admissions.get("test_scores_accepted", [])

    for score_info in test_scores:
        test_name = score_info.get("test", "")
        p25 = score_info.get("percentile_25")
        p75 = score_info.get("percentile_75")
        avg = score_info.get("avg_score")

        if test_name == "SAT Critical Reading":
            if p25 is not None:
                metadata["sat_verbal_25"] = p25
            if p75 is not None:
                metadata["sat_verbal_75"] = p75
            if avg is not None:
                metadata["sat_verbal_avg"] = avg
        elif test_name == "SAT Math":
            if p25 is not None:
                metadata["sat_math_25"] = p25
            if p75 is not None:
                metadata["sat_math_75"] = p75
            if avg is not None:
                metadata["sat_math_avg"] = avg
        elif test_name == "ACT Composite":
            if p25 is not None:
                metadata["act_composite_25"] = p25
            if p75 is not None:
                metadata["act_composite_75"] = p75
            if avg is not None:
                metadata["act_composite_avg"] = avg

    return metadata
