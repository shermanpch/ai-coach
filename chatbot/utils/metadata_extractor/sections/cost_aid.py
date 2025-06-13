"""
Cost and financial aid metadata extraction for Peterson university data.
"""

from typing import Any, Dict


def extract_cost_aid_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract cost and financial aid metadata fields.

    Fields extracted:
    - tuition_in_state, tuition_out_of_state, tuition_private: Tuition by category
    - room_and_board: Room and board costs
    - full_time_student_fees: Additional student fees
    - avg_financial_aid_package: General financial aid package
    - avg_freshman_financial_aid_package: Freshman-specific aid
    - avg_international_financial_aid_package: International student aid
    - avg_loan_aid, avg_grant_aid, avg_scholarship_and_grant_aid_awarded: Aid breakdown
    - percentage_need_receive_financial_aid: Percentage receiving aid (0-1 decimal)
    - avg_percentage_of_financial_need_met: Average need met (0-1 decimal)
    - percentage_students_need_fully_met: Percentage with full need met (0-1 decimal)

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with cost and aid metadata
    """
    metadata = {}

    # Tuition and fees information
    tuition_fees = json_record.get("tuition_and_fees", {})

    # Tuition by category
    for tuition_info in tuition_fees.get("tuition", []):
        category = tuition_info.get("category")
        amount = tuition_info.get("amount")
        if amount is not None:
            if category == "In-state":
                metadata["tuition_in_state"] = amount
            elif category == "Out-of-state":
                metadata["tuition_out_of_state"] = amount
            elif category == "Private":
                metadata["tuition_private"] = amount

    # Fees breakdown
    for fee_info in tuition_fees.get("fees", []):
        category = fee_info.get("category")
        amount = fee_info.get("amount")
        if amount is not None:
            if category == "Room & board":
                metadata["room_and_board"] = amount
            elif category == "Full-time student fees":
                metadata["full_time_student_fees"] = amount

    # Financial aid - comprehensive package information
    financial_aid = json_record.get("financial_aid", {})

    # Package statistics
    package_stats = financial_aid.get("package_stats", {})
    metadata["avg_financial_aid_package"] = package_stats.get(
        "avg_financial_aid_package"
    )
    metadata["avg_freshman_financial_aid_package"] = package_stats.get(
        "avg_freshman_financial_aid_package"
    )
    metadata["avg_international_financial_aid_package"] = package_stats.get(
        "avg_international_financial_aid_package"
    )

    # Aid amounts breakdown
    amounts = financial_aid.get("amounts", {})
    metadata["avg_loan_aid"] = amounts.get("avg_loan_aid")
    metadata["avg_grant_aid"] = amounts.get("avg_grant_aid")
    metadata["avg_scholarship_and_grant_aid_awarded"] = amounts.get(
        "avg_scholarship_and_grant_aid_awarded"
    )

    # Coverage statistics - convert percentages to 0-1 decimals
    coverage_stats = financial_aid.get("coverage_stats", {})

    percentage_need_receive_aid = coverage_stats.get(
        "percentage_need_receive_financial_aid"
    )
    if percentage_need_receive_aid is not None:
        metadata["percentage_need_receive_financial_aid"] = (
            percentage_need_receive_aid / 100.0
        )

    avg_percentage_need_met = coverage_stats.get("avg_percentage_of_financial_need_met")
    if avg_percentage_need_met is not None:
        metadata["avg_percentage_of_financial_need_met"] = (
            avg_percentage_need_met / 100.0
        )

    percentage_need_fully_met = coverage_stats.get("percentage_students_need_fully_met")
    if percentage_need_fully_met is not None:
        metadata["percentage_students_need_fully_met"] = (
            percentage_need_fully_met / 100.0
        )

    return metadata
