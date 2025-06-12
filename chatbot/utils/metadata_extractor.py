from typing import Any, Dict


def extract_metadata_from_json(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant flat metadata from a university's JSON object.
    Example fields: university_name, state, city, zip_code, application_fee,
                    avg_high_school_gpa, sat_math_25, sat_math_75,
                    sat_reading_25, sat_reading_75.
    Handle missing values appropriately (e.g., omit key or use None,
    consistent with how ChromaDB filters will be used).

    Args:
        json_record: A dictionary containing university data

    Returns:
        A dictionary with flattened metadata suitable for ChromaDB
    """
    metadata = {}
    metadata["university_name"] = json_record.get("university_name")

    # Location
    location_contact = json_record.get("location_contact", {}).get("address", {})
    metadata["city"] = location_contact.get("city")
    metadata["state"] = location_contact.get("state")
    metadata["zip_code"] = location_contact.get("zip_code")

    # Admissions
    admissions = json_record.get("admissions", {})
    applying_info = admissions.get("applying", {})
    if applying_info.get("application_fee") is not None:
        metadata["application_fee"] = applying_info.get("application_fee")
    if applying_info.get("avg_high_school_gpa") is not None:
        metadata["avg_high_school_gpa"] = applying_info.get("avg_high_school_gpa")

    # Overall admissions stats
    overall_admissions = admissions.get("overall", {})
    if overall_admissions.get("acceptance_rate") is not None:
        metadata["acceptance_rate"] = overall_admissions.get("acceptance_rate")

    # Test scores
    test_scores = admissions.get("test_scores_accepted", [])
    for score_info in test_scores:
        test_name = score_info.get("test")
        if test_name == "SAT Critical Reading":
            if score_info.get("percentile_25") is not None:
                metadata["sat_reading_25"] = score_info.get("percentile_25")
            if score_info.get("percentile_75") is not None:
                metadata["sat_reading_75"] = score_info.get("percentile_75")
        elif test_name == "SAT Math":
            if score_info.get("percentile_25") is not None:
                metadata["sat_math_25"] = score_info.get("percentile_25")
            if score_info.get("percentile_75") is not None:
                metadata["sat_math_75"] = score_info.get("percentile_75")

    # Skip majors field since it's a list and ChromaDB doesn't support list metadata

    # Tuition information
    tuition_fees = json_record.get("tuition_and_fees", {})
    for tuition_info in tuition_fees.get("tuition", []):
        if (
            tuition_info.get("category") == "In-state"
            and tuition_info.get("amount") is not None
        ):
            metadata["tuition_in_state"] = tuition_info.get("amount")
        elif (
            tuition_info.get("category") == "Out-of-state"
            and tuition_info.get("amount") is not None
        ):
            metadata["tuition_out_of_state"] = tuition_info.get("amount")

    # Room and board information
    for fee_info in tuition_fees.get("fees", []):
        if (
            fee_info.get("category") == "Room & board"
            and fee_info.get("amount") is not None
        ):
            metadata["room_and_board"] = fee_info.get("amount")

    # Housing information
    campus_life = json_record.get("campus_life", {})
    housing_info = campus_life.get("housing", {})
    if housing_info.get("percent_undergrads_in_college_housing") is not None:
        metadata["percent_undergrads_in_housing"] = housing_info.get(
            "percent_undergrads_in_college_housing"
        )
    if housing_info.get("college_owned_housing") is not None:
        metadata["has_college_housing"] = housing_info.get("college_owned_housing")

    # Faculty information
    faculty_info = json_record.get("faculty", {})
    if (
        faculty_info.get("total_faculty") is not None
        and faculty_info.get("total_faculty") > 0
    ):
        metadata["total_faculty"] = faculty_info.get("total_faculty")

    # Parse student-faculty ratio if available
    ratio_str = faculty_info.get("student_faculty_ratio", "")
    if ratio_str and ":" in ratio_str and ratio_str != "0:1":
        try:
            student_part = ratio_str.split(":")[0]
            if student_part.isdigit():
                metadata["student_faculty_ratio"] = int(student_part)
        except (ValueError, IndexError):
            pass

    # Remove keys with None values to keep metadata clean for ChromaDB
    return {k: v for k, v in metadata.items() if v is not None}
