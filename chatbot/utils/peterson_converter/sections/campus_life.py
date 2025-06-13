"""
Campus Life section generator for Peterson university markdown conversion.
"""

from typing import Dict, List

from ..formatters import get_value


def generate_campus_life_section(uni_data: Dict) -> List[str]:
    """Generate the Campus Life section."""
    lines = ["## Campus Life", ""]

    campus_life = uni_data.get("campus_life", {})

    # Student Body Information (when available)
    student_body = campus_life.get("student_body", {})
    if student_body:
        lines.append("### Student Body")
        lines.append("")

        total_undergrad = get_value(student_body, "total_undergrad_students")
        if total_undergrad != "Not Reported":
            lines.append(f"- **Total Undergraduate Students:** {total_undergrad}")

        intl_pct = get_value(student_body, "international_students_percentage")
        if intl_pct != "Not Reported":
            lines.append(f"- **International Students:** {intl_pct}%")

        out_of_state_pct = get_value(student_body, "out_of_state_students_percentage")
        if out_of_state_pct != "Not Reported":
            lines.append(f"- **Out-of-State Students:** {out_of_state_pct}%")

        gender_dist = student_body.get("gender_distribution", {})
        if gender_dist:
            male_pct = get_value(gender_dist, "male")
            female_pct = get_value(gender_dist, "female")
            if male_pct != "Not Reported" and female_pct != "Not Reported":
                lines.append(
                    f"- **Gender Distribution:** Male: {male_pct}%, Female: {female_pct}%"
                )

        lines.append("")

    # Housing
    lines.append("### Housing")
    lines.append("")

    housing = campus_life.get("housing", {})
    lines.append(
        f"- **College-Owned Housing Available:** {get_value(housing, 'college_owned_housing')}"
    )
    lines.append(
        f"- **Housing Requirements:** {get_value(housing, 'housing_requirements')}"
    )

    housing_options = housing.get("housing_options", [])
    if housing_options:
        options_str = ", ".join(housing_options)
        lines.append(f"- **Housing Options:** {options_str}")
    else:
        lines.append("- **Housing Options:** Not Reported")

    pct_housing = get_value(housing, "percent_undergrads_in_college_housing")
    if pct_housing != "Not Reported":
        lines.append(f"- **Percent Undergrads in College Housing:** {pct_housing}%")
    else:
        lines.append(f"- **Percent Undergrads in College Housing:** {pct_housing}")

    lines.append("")

    # Student Activities
    lines.append("### Student Activities")
    lines.append("")

    activities = campus_life.get("student_activities", [])
    if activities:
        for activity in activities:
            lines.append(f"- {activity}")
    else:
        lines.append("- Not Reported")

    lines.append("")

    # Student Services
    lines.append("### Student Services")
    lines.append("")

    services = campus_life.get("student_services", [])
    if services:
        for service in services:
            lines.append(f"- {service}")
    else:
        lines.append("- Not Reported")

    lines.append("")

    # Student Organizations
    lines.append("### Student Organizations")
    lines.append("")

    organizations = campus_life.get("student_organizations", [])
    if organizations:
        for org in organizations:
            lines.append(f"- {org}")
    else:
        lines.append("- Not Reported")

    # Most Popular Organizations (when available)
    most_popular = campus_life.get("most_popular_organizations", [])
    if most_popular:
        lines.append("")
        lines.append("#### Most Popular Organizations")
        lines.append("")
        for org in most_popular:
            lines.append(f"- {org}")

    lines.append("")

    # Campus Events (when available)
    campus_events = campus_life.get("campus_events", [])
    if campus_events:
        lines.append("### Campus Events")
        lines.append("")
        for event in campus_events:
            lines.append(f"- {event}")
        lines.append("")

    # Campus Security and Safety
    lines.append("### Campus Security and Safety")
    lines.append("")

    security = campus_life.get("campus_security_and_safety", [])
    if isinstance(security, list):
        # Handle list format (most common)
        if security:
            for item in security:
                lines.append(f"- {item}")
        else:
            lines.append("- Not Reported")
    elif isinstance(security, dict):
        # Handle nested dict format (less common but present)
        security_items = []

        if get_value(security, "emergency_services") != "Not Reported":
            emergency = get_value(security, "emergency_services")
            if emergency == "True" or emergency is True:
                security_items.append("24-hour emergency telephone/alarm services")
            elif emergency != "False" and emergency is not False:
                security_items.append(f"Emergency services: {emergency}")

        if get_value(security, "patrols") != "Not Reported":
            patrols = get_value(security, "patrols")
            if patrols == "True" or patrols is True:
                security_items.append("24-hour patrols by trained officers")
            elif patrols != "False" and patrols is not False:
                security_items.append(f"Patrols: {patrols}")

        if get_value(security, "student_patrols") != "Not Reported":
            student_patrols = get_value(security, "student_patrols")
            if student_patrols == "True" or student_patrols is True:
                security_items.append("Student patrols")

        if get_value(security, "transport_services") != "Not Reported":
            transport = get_value(security, "transport_services")
            if transport == "True" or transport is True:
                security_items.append("Late-night transport/escort services")
            elif transport != "False" and transport is not False:
                security_items.append(f"Transport services: {transport}")

        if get_value(security, "dormitory_entrances") != "Not Reported":
            dorm_entrances = get_value(security, "dormitory_entrances")
            if dorm_entrances == "True" or dorm_entrances is True:
                security_items.append("Controlled dormitory entrances")

        if get_value(security, "other_security") != "Not Reported":
            other = get_value(security, "other_security")
            security_items.append(f"Additional security: {other}")

        if security_items:
            for item in security_items:
                lines.append(f"- {item}")
        else:
            lines.append("- Not Reported")
    else:
        lines.append("- Not Reported")

    lines.append("")
    return lines
