"""
Admissions section generator for Peterson university markdown conversion.
"""

from typing import Dict, List

from projectutils.logger import setup_logger

from ..formatters import get_value

logger = setup_logger(__file__)


def generate_admissions_section(
    uni_data: Dict, university_name: str = "N/A"
) -> List[str]:
    """Generate the Admissions section."""
    lines = ["## Admissions", ""]

    admissions = uni_data.get("admissions", {})

    # Overview
    lines.append("### Overview")
    lines.append("")

    overall = admissions.get("overall", {})
    acceptance_rate = get_value(overall, "acceptance_rate")
    if acceptance_rate != "Not Reported":
        lines.append(f"- **Acceptance Rate:** {acceptance_rate}%")
    else:
        lines.append(f"- **Acceptance Rate:** {acceptance_rate}")

    lines.append(f"- **Applied:** {get_value(overall, 'applied')}")
    lines.append(f"- **Accepted:** {get_value(overall, 'accepted')}")
    lines.append(f"- **Enrolled:** {get_value(overall, 'enrolled')}")

    # By Gender
    by_gender = admissions.get("by_gender", {})

    female = by_gender.get("female", {})
    lines.append(f"- **Female Applied:** {get_value(female, 'applied')}")
    lines.append(f"- **Female Accepted:** {get_value(female, 'accepted')}")
    female_rate = get_value(female, "acceptance_rate")
    if female_rate != "Not Reported":
        lines.append(f"- **Female Acceptance Rate:** {female_rate}%")
    else:
        lines.append(f"- **Female Acceptance Rate:** {female_rate}")

    male = by_gender.get("male", {})
    lines.append(f"- **Male Applied:** {get_value(male, 'applied')}")
    lines.append(f"- **Male Accepted:** {get_value(male, 'accepted')}")
    male_rate = get_value(male, "acceptance_rate")
    if male_rate != "Not Reported":
        lines.append(f"- **Male Acceptance Rate:** {male_rate}%")
    else:
        lines.append(f"- **Male Acceptance Rate:** {male_rate}")

    lines.append("")

    # Application Details
    lines.append("### Application Details")
    lines.append("")

    applying = admissions.get("applying", {})
    app_fee = get_value(applying, "application_fee")
    if app_fee != "Not Reported":
        lines.append(f"- **Application Fee:** ${app_fee}")
    else:
        lines.append(f"- **Application Fee:** {app_fee}")

    lines.append(
        f"- **Average High School GPA:** {get_value(applying, 'avg_high_school_gpa')}"
    )
    lines.append("")

    # Requirements
    lines.append("### Requirements")
    lines.append("")

    requirements = admissions.get("requirements", [])
    if requirements:
        for req_category_obj in requirements:
            # Handle malformed data where strings might be in the list
            if not isinstance(req_category_obj, dict):
                logger.warning(
                    f"Skipping malformed requirement entry for {university_name}: {req_category_obj}"
                )
                continue

            category = get_value(req_category_obj, "category")
            lines.append(f"#### {category}")
            lines.append("")

            items = req_category_obj.get("items", [])
            for item in items:
                lines.append(f"- {item}")

            lines.append("")
    else:
        lines.append("No specific requirements reported.")
        lines.append("")

    # Application Deadlines
    lines.append("### Application Deadlines")
    lines.append("")

    deadlines = admissions.get("application_deadlines", [])
    if deadlines:
        for deadline_obj in deadlines:
            deadline_type = get_value(deadline_obj, "type")
            closing = get_value(deadline_obj, "application_closing")
            notification = get_value(deadline_obj, "notification_date")
            rolling = get_value(deadline_obj, "rolling_admissions")

            lines.append(
                f"- **{deadline_type}:** Closing Date: {closing}, Notification: {notification}, Rolling Admissions: {rolling}"
            )
    else:
        lines.append("No application deadline information reported.")

    lines.append("")

    # Test Scores Accepted
    lines.append("### Test Scores Accepted")
    lines.append("")

    test_scores = admissions.get("test_scores_accepted", [])
    if test_scores:
        for score_obj in test_scores:
            test_name = get_value(score_obj, "test")
            avg = get_value(score_obj, "avg_score")
            p25 = get_value(score_obj, "percentile_25")
            p75 = get_value(score_obj, "percentile_75")

            lines.append(
                f"- **{test_name}:** Average: {avg}, 25th Percentile: {p25}, 75th Percentile: {p75}"
            )
    else:
        lines.append("- No specific test score data reported.")

    lines.append("")
    return lines
