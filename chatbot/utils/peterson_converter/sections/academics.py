"""
Academics section generator for Peterson university markdown conversion.
"""

from typing import Dict, List

from ..formatters import get_value


def generate_academics_section(uni_data: Dict) -> List[str]:
    """Generate the Academics section."""
    lines = ["## Academics", ""]

    # Majors and Degrees
    lines.append("### Majors and Degrees")
    lines.append("")

    majors_and_degrees = uni_data.get("majors_and_degrees", [])
    if majors_and_degrees:
        for major_category_obj in majors_and_degrees:
            category = get_value(major_category_obj, "category")
            lines.append(f"#### {category}")
            lines.append("")

            programs = major_category_obj.get("programs", [])
            for program_obj in programs:
                program_name = get_value(program_obj, "name")
                offers_bachelors = get_value(program_obj, "offers_bachelors")
                offers_associates = get_value(program_obj, "offers_associate")

                lines.append(
                    f"- {program_name} (Bachelors: {offers_bachelors}, Associates: {offers_associates})"
                )

            lines.append("")
    else:
        lines.append("No major and degree information reported.")
        lines.append("")

    # Faculty
    lines.append("### Faculty")
    lines.append("")

    faculty = uni_data.get("faculty", {})
    lines.append(f"- **Total Faculty:** {get_value(faculty, 'total_faculty')}")
    lines.append(
        f"- **Student-Faculty Ratio:** {get_value(faculty, 'student_faculty_ratio')}"
    )

    employment = faculty.get("employment", {})
    lines.append(f"- **Full-time Faculty:** {get_value(employment, 'full_time')}")
    lines.append(f"- **Part-time Faculty:** {get_value(employment, 'part_time')}")

    gender = faculty.get("gender", {})
    lines.append(f"- **Male Faculty:** {get_value(gender, 'male')}")
    lines.append(f"- **Female Faculty:** {get_value(gender, 'female')}")

    lines.append("")
    return lines
