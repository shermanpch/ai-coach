"""
Tuition and Financial Aid section generator for Peterson university markdown conversion.
"""

from typing import Dict, List

from ..formatters import get_value


def generate_tuition_section(uni_data: Dict) -> List[str]:
    """Generate the Tuition and Financial Aid section."""
    lines = ["## Tuition and Financial Aid", ""]

    tuition_fees = uni_data.get("tuition_and_fees", {})

    # Tuition & Fees
    lines.append("### Tuition & Fees")
    lines.append("")

    tuition = tuition_fees.get("tuition", [])
    for tuition_item in tuition:
        category = get_value(tuition_item, "category")
        amount = get_value(tuition_item, "amount")
        if amount != "Not Reported":
            lines.append(f"- **Tuition ({category}):** ${amount}")
        else:
            lines.append(f"- **Tuition ({category}):** {amount}")

    fees = tuition_fees.get("fees", [])
    for fee_item in fees:
        category = get_value(fee_item, "category")
        amount = get_value(fee_item, "amount")
        if amount != "Not Reported":
            lines.append(f"- **Fees ({category}):** ${amount}")
        else:
            lines.append(f"- **Fees ({category}):** {amount}")

    other_considerations = get_value(tuition_fees, "other_payment_considerations")
    if other_considerations != "Not Reported":
        lines.append(f"- **Other Payment Considerations:** {other_considerations}")

    lines.append("")

    # Financial Aid Overview
    lines.append("### Financial Aid Overview")
    lines.append("")

    financial_aid = uni_data.get("financial_aid", {})

    # Package Stats
    package_stats = financial_aid.get("package_stats", {})
    avg_aid = get_value(package_stats, "avg_financial_aid_package")
    if avg_aid != "Not Reported":
        lines.append(f"- **Average Financial Aid Package:** ${avg_aid}")
    else:
        lines.append(f"- **Average Financial Aid Package:** {avg_aid}")

    avg_freshman_aid = get_value(package_stats, "avg_freshman_financial_aid_package")
    if avg_freshman_aid != "Not Reported":
        lines.append(
            f"- **Average Freshman Financial Aid Package:** ${avg_freshman_aid}"
        )
    else:
        lines.append(
            f"- **Average Freshman Financial Aid Package:** {avg_freshman_aid}"
        )

    avg_intl_aid = get_value(package_stats, "avg_international_financial_aid_package")
    if avg_intl_aid != "Not Reported":
        lines.append(
            f"- **Average International Financial Aid Package:** ${avg_intl_aid}"
        )
    else:
        lines.append(
            f"- **Average International Financial Aid Package:** {avg_intl_aid}"
        )

    # Amounts
    amounts = financial_aid.get("amounts", {})
    avg_loan = get_value(amounts, "avg_loan_aid")
    if avg_loan != "Not Reported":
        lines.append(f"- **Average Loan Aid:** ${avg_loan}")
    else:
        lines.append(f"- **Average Loan Aid:** {avg_loan}")

    avg_grant = get_value(amounts, "avg_grant_aid")
    if avg_grant != "Not Reported":
        lines.append(f"- **Average Grant Aid:** ${avg_grant}")
    else:
        lines.append(f"- **Average Grant Aid:** {avg_grant}")

    avg_scholarship = get_value(amounts, "avg_scholarship_and_grant_aid_awarded")
    if avg_scholarship != "Not Reported":
        lines.append(
            f"- **Average Scholarship and Grant Aid Awarded:** ${avg_scholarship}"
        )
    else:
        lines.append(
            f"- **Average Scholarship and Grant Aid Awarded:** {avg_scholarship}"
        )

    # Coverage Stats
    coverage_stats = financial_aid.get("coverage_stats", {})

    pct_need_receive = get_value(
        coverage_stats, "percentage_need_receive_financial_aid"
    )
    if pct_need_receive != "Not Reported":
        lines.append(
            f"- **Percentage of Students Receiving Financial Aid Who Had Need:** {pct_need_receive}%"
        )
    else:
        lines.append(
            f"- **Percentage of Students Receiving Financial Aid Who Had Need:** {pct_need_receive}"
        )

    avg_pct_need_met = get_value(coverage_stats, "avg_percentage_of_financial_need_met")
    if avg_pct_need_met != "Not Reported":
        lines.append(
            f"- **Average Percentage of Financial Need Met:** {avg_pct_need_met}%"
        )
    else:
        lines.append(
            f"- **Average Percentage of Financial Need Met:** {avg_pct_need_met}"
        )

    pct_fully_met = get_value(coverage_stats, "percentage_students_need_fully_met")
    if pct_fully_met != "Not Reported":
        lines.append(
            f"- **Percentage of Students Whose Financial Need Was Fully Met:** {pct_fully_met}%"
        )
    else:
        lines.append(
            f"- **Percentage of Students Whose Financial Need Was Fully Met:** {pct_fully_met}"
        )

    lines.append("")
    return lines
