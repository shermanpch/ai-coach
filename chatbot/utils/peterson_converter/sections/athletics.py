"""
Athletics section generator for Peterson university markdown conversion.
"""

from typing import Dict, List

from ..formatters import format_sport


def generate_athletics_section(uni_data: Dict) -> List[str]:
    """Generate the Athletics section."""
    lines = ["## Athletics", ""]

    athletics = uni_data.get("athletics", {})

    # Men's Sports
    lines.append("### Men's Sports")
    lines.append("")

    mens_sports = athletics.get("Men's Sports", [])
    if mens_sports:
        for sport_obj in mens_sports:
            lines.append(format_sport(sport_obj))
    else:
        lines.append("- No men's sports data reported.")

    lines.append("")

    # Women's Sports
    lines.append("### Women's Sports")
    lines.append("")

    womens_sports = athletics.get("Women's Sports", [])
    if womens_sports:
        for sport_obj in womens_sports:
            lines.append(format_sport(sport_obj))
    else:
        lines.append("- No women's sports data reported.")

    lines.append("")
    return lines
