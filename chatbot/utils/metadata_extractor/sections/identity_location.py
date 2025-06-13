"""
Identity and location metadata extraction for Peterson university data.
"""

from typing import Any, Dict

from ..utils import derive_region_from_state


def extract_identity_location_metadata(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract identity and location metadata fields.

    Fields extracted:
    - url: Primary identifier/link to Peterson's page
    - university_name: Secondary identifier/display name
    - state, city, zip_code, country: Location information
    - region: Derived US region from state (★ derived field)

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with identity and location metadata
    """
    metadata = {}

    # URL - primary identifier
    metadata["url"] = json_record.get("url")

    # University name - secondary identifier
    metadata["university_name"] = json_record.get("university_name")

    # Location information
    location_contact = json_record.get("location_contact", {}).get("address", {})
    metadata["state"] = location_contact.get("state")
    metadata["city"] = location_contact.get("city")
    metadata["zip_code"] = location_contact.get("zip_code")
    metadata["country"] = location_contact.get("country")

    # Derived region from state ★
    state = metadata.get("state")
    if state:
        metadata["region"] = derive_region_from_state(state)

    return metadata
