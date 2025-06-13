"""
Data Completeness section generator for Peterson university markdown conversion.
"""

from typing import Dict, List


def generate_data_completeness_section(uni_data: Dict) -> List[str]:
    """Generate a Data Completeness section showing available information."""
    lines = ["## Data Completeness", ""]
    lines.append(
        "This section shows which data categories are available for this university:"
    )
    lines.append("")

    # Check major sections
    sections_available = []
    sections_missing = []

    # Location (should always be available)
    location_contact = uni_data.get("location_contact", {})
    if location_contact:
        sections_available.append("✅ Location and Contact Information")
    else:
        sections_missing.append("❌ Location and Contact Information")

    # Academics
    majors_and_degrees = uni_data.get("majors_and_degrees", [])
    faculty = uni_data.get("faculty", {})
    if majors_and_degrees or faculty:
        sections_available.append("✅ Academic Information")
    else:
        sections_missing.append("❌ Academic Information")

    # Admissions
    admissions = uni_data.get("admissions", {})
    if admissions:
        sections_available.append("✅ Admissions Information")
    else:
        sections_missing.append("❌ Admissions Information")

    # Tuition and Financial Aid
    tuition_fees = uni_data.get("tuition_and_fees", {})
    financial_aid = uni_data.get("financial_aid", {})
    if tuition_fees or financial_aid:
        sections_available.append("✅ Tuition and Financial Aid")
    else:
        sections_missing.append("❌ Tuition and Financial Aid")

    # Campus Life
    campus_life = uni_data.get("campus_life", {})
    if campus_life:
        sections_available.append("✅ Campus Life Information")
    else:
        sections_missing.append("❌ Campus Life Information")

    # Athletics
    athletics = uni_data.get("athletics", {})
    if athletics:
        sections_available.append("✅ Athletics Information")
    else:
        sections_missing.append("❌ Athletics Information")

    # Add available sections
    for section in sections_available:
        lines.append(section)

    # Add missing sections
    for section in sections_missing:
        lines.append(section)

    lines.append("")

    # Detailed subsection availability
    lines.append("### Detailed Data Availability")
    lines.append("")

    # Campus Life details
    if campus_life:
        housing = campus_life.get("housing", {})
        student_activities = campus_life.get("student_activities", [])
        student_services = campus_life.get("student_services", [])
        student_organizations = campus_life.get("student_organizations", [])
        security = campus_life.get("campus_security_and_safety", [])
        most_popular = campus_life.get("most_popular_organizations", [])
        events = campus_life.get("campus_events", [])
        student_body = campus_life.get("student_body", {})

        lines.append("**Campus Life Details:**")
        lines.append(f"- Housing Information: {'✅' if housing else '❌'}")
        lines.append(f"- Student Activities: {'✅' if student_activities else '❌'}")
        lines.append(f"- Student Services: {'✅' if student_services else '❌'}")
        lines.append(
            f"- Student Organizations: {'✅' if student_organizations else '❌'}"
        )
        lines.append(f"- Campus Security: {'✅' if security else '❌'}")
        lines.append(f"- Most Popular Organizations: {'✅' if most_popular else '❌'}")
        lines.append(f"- Campus Events: {'✅' if events else '❌'}")
        lines.append(f"- Student Body Demographics: {'✅' if student_body else '❌'}")
        lines.append("")

    # Admissions details
    if admissions:
        overall = admissions.get("overall", {})
        by_gender = admissions.get("by_gender", {})
        requirements = admissions.get("requirements", [])
        deadlines = admissions.get("application_deadlines", [])
        test_scores = admissions.get("test_scores_accepted", [])

        lines.append("**Admissions Details:**")
        lines.append(f"- Overall Statistics: {'✅' if overall else '❌'}")
        lines.append(f"- Gender-based Statistics: {'✅' if by_gender else '❌'}")
        lines.append(f"- Requirements: {'✅' if requirements else '❌'}")
        lines.append(f"- Application Deadlines: {'✅' if deadlines else '❌'}")
        lines.append(f"- Test Score Information: {'✅' if test_scores else '❌'}")
        lines.append("")

    # Athletics details
    if athletics:
        mens_sports = athletics.get("Men's Sports", [])
        womens_sports = athletics.get("Women's Sports", [])

        lines.append("**Athletics Details:**")
        lines.append(
            f"- Men's Sports: {'✅' if mens_sports else '❌'} ({len(mens_sports)} sports)"
        )
        lines.append(
            f"- Women's Sports: {'✅' if womens_sports else '❌'} ({len(womens_sports)} sports)"
        )
        lines.append("")

    return lines
