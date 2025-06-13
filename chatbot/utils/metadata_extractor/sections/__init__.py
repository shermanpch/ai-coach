"""
Section-specific metadata extraction functions.
"""

from .academic import extract_academic_metadata
from .admissions import extract_admissions_metadata
from .athletics import extract_athletics_metadata
from .cost_aid import extract_cost_aid_metadata
from .housing import extract_housing_metadata
from .identity_location import extract_identity_location_metadata
from .student_body import extract_student_body_metadata

__all__ = [
    "extract_academic_metadata",
    "extract_admissions_metadata",
    "extract_athletics_metadata",
    "extract_cost_aid_metadata",
    "extract_housing_metadata",
    "extract_identity_location_metadata",
    "extract_student_body_metadata",
]
