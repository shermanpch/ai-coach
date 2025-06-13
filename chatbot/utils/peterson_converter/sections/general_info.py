"""
General Information section generator for Peterson university markdown conversion.
"""

from typing import Dict, List

from ..formatters import get_value


def generate_general_info_section(uni_data: Dict) -> List[str]:
    """Generate the General Information section."""
    lines = ["## General Information", ""]

    # Location and Address
    location_contact = uni_data.get("location_contact", {})
    address = location_contact.get("address", {})

    city = get_value(address, "city")
    state = get_value(address, "state")
    country = get_value(address, "country")
    street = get_value(address, "street")
    zip_code = get_value(address, "zip_code")

    lines.append(f"- **Location:** {city}, {state}, {country}")
    lines.append(f"- **Address:** {street}, {city}, {state} {zip_code}")

    # Contact Information
    contact = location_contact.get("contact", {})
    phone = get_value(contact, "phone")
    fax = get_value(contact, "fax")
    email = get_value(contact, "email")
    contact_name = get_value(contact, "name")
    contact_title = get_value(contact, "title")

    lines.append(f"- **Phone:** {phone}")
    lines.append(f"- **Fax:** {fax}")
    lines.append(f"- **Email:** {email}")

    # Handle contact person
    if contact_name != "Not Reported" and contact_title != "Not Reported":
        lines.append(f"- **Contact Person:** {contact_name} ({contact_title})")
    elif contact_name != "Not Reported":
        lines.append(f"- **Contact Person:** {contact_name}")
    else:
        lines.append("- **Contact Person:** Not Reported")

    lines.append("")
    return lines
