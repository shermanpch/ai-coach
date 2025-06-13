import functools
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

load_dotenv()

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def slugify(text: str) -> str:
    """
    Convert a string (university name) to a URL-friendly slug.

    Args:
        text (str): The text to slugify

    Returns:
        str: The slugified string (e.g., "Swarthmore College" -> "swarthmore-college")
    """
    if not text or text == "Not Reported":
        return "unknown"

    # Convert to lowercase
    text = text.lower()
    # Replace spaces and non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")

    return text


def generate_unique_id(uni_data: Dict, index: int) -> str:
    """
    Generate a unique identifier for a university based on its key attributes.

    Args:
        uni_data (Dict): The university data dictionary
        index (int): The index position in the original JSON array

    Returns:
        str: A unique identifier string
    """
    # Extract key identifying information
    university_name = uni_data.get("university_name", "Unknown")

    location_contact = uni_data.get("location_contact", {})
    address = location_contact.get("address", {})
    city = address.get("city", "")
    state = address.get("state", "")
    zip_code = address.get("zip_code", "")

    # Create a string that uniquely identifies this university
    identifier_string = f"{university_name}|{city}|{state}|{zip_code}|{index}"

    # Generate MD5 hash
    unique_id = hashlib.md5(identifier_string.encode("utf-8")).hexdigest()

    return unique_id


def get_value(data: Dict, key: str, default: str = "Not Reported") -> str:
    """
    Safely retrieve a value from a dictionary with proper formatting.

    Args:
        data (Dict): The dictionary to retrieve from
        key (str): The key to look for
        default (str): The default value if key not found or value is None/empty

    Returns:
        str: The formatted value
    """
    if not isinstance(data, dict):
        return default

    value = data.get(key)

    # Handle None or empty string
    if value is None or value == "":
        return default

    # Handle boolean values
    if isinstance(value, bool):
        return "Yes" if value else "No"

    # Handle lists
    if isinstance(value, list):
        if not value:  # Empty list
            return default
        # Join string lists with commas
        if all(isinstance(item, str) for item in value):
            return ", ".join(value)
        else:
            return default

    # Return the value as string
    return str(value)


def format_sport(sport_obj: Dict) -> str:
    """Format a sport object into a markdown line."""
    sport_name = get_value(sport_obj, "sport")
    intercollegiate = get_value(sport_obj, "intercollegiate")
    scholarship = get_value(sport_obj, "scholarship")
    intramural = get_value(sport_obj, "intramural")

    return f"- **{sport_name}:** Intercollegiate: {intercollegiate}, Scholarship: {scholarship}, Intramural: {intramural}"


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
    email = get_value(contact, "email")
    contact_name = get_value(contact, "name")
    contact_title = get_value(contact, "title")

    lines.append(f"- **Phone:** {phone}")
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


def generate_campus_life_section(uni_data: Dict) -> List[str]:
    """Generate the Campus Life section."""
    lines = ["## Campus Life", ""]

    campus_life = uni_data.get("campus_life", {})

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

    lines.append("")

    # Campus Security and Safety
    lines.append("### Campus Security and Safety")
    lines.append("")

    security = campus_life.get("campus_security_and_safety", [])
    if security:
        for item in security:
            lines.append(f"- {item}")
    else:
        lines.append("- Not Reported")

    lines.append("")
    return lines


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


def convert_to_markdown():
    """Convert all Peterson university data to individual Markdown files"""
    logger.info("Starting Peterson data to Markdown conversion...")

    # Define file paths relative to project root
    input_file = PROJECT_ROOT / "data" / "cleaned" / "peterson_data.json"
    output_dir = PROJECT_ROOT / "data" / "chatbot" / "peterson_data"
    mapping_file = output_dir / "id_mapping.json"

    # Validate input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Load university data
    universities = load_peterson_data(input_file)

    # Process each university
    successful_conversions = 0
    failed_conversions = 0
    id_mapping = {}

    for i, uni_data in enumerate(universities):
        try:
            university_name = uni_data.get("university_name", "N/A")

            # Generate unique identifier
            unique_id = generate_unique_id(uni_data, i)

            # Generate filename
            filename = slugify(university_name) + ".md"
            filepath = output_dir / filename

            # Store mapping information
            id_mapping[unique_id] = {
                "university_name": university_name,
                "filename": filename,
                "json_index": i,
                "slug": slugify(university_name),
            }

            # Generate markdown content
            markdown_content = []

            # Header with unique identifier
            markdown_content.append(f"# {university_name}")
            markdown_content.append("")
            markdown_content.append(f"**Document ID:** `{unique_id}`")
            markdown_content.append("")

            # Generate sections
            markdown_content.extend(generate_general_info_section(uni_data))
            markdown_content.extend(generate_academics_section(uni_data))
            markdown_content.extend(
                generate_admissions_section(uni_data, university_name)
            )
            markdown_content.extend(generate_tuition_section(uni_data))
            markdown_content.extend(generate_campus_life_section(uni_data))
            markdown_content.extend(generate_athletics_section(uni_data))

            # Write to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))

            successful_conversions += 1

            # Progress update
            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i + 1}/{len(universities)} universities...")

        except Exception as e:
            logger.error(f"Failed to convert {university_name}: {e}")
            failed_conversions += 1

    # Write ID mapping file
    try:
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(id_mapping, f, indent=2, ensure_ascii=False)
        logger.info(f"ID mapping file created: {mapping_file}")
    except Exception as e:
        logger.error(f"Failed to create ID mapping file: {e}")

    # Log summary
    logger.info("Conversion complete!")
    logger.info("Summary:")
    logger.info(f"  Total universities: {len(universities)}")
    logger.info(f"  Successfully converted: {successful_conversions}")
    logger.info(f"  Failed conversions: {failed_conversions}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info(f"  ID mapping file: {mapping_file}")


def main():
    """Main function to orchestrate the Peterson data to Markdown conversion"""
    logger.info("Peterson Data to Markdown Converter - Starting...")

    convert_to_markdown()

    logger.info("Peterson Data to Markdown Converter - Complete!")


@functools.lru_cache(maxsize=1)
def load_peterson_data(input_file: Path) -> List[Dict]:
    """
    Load university data from the cleaned Peterson JSON file.

    This function is cached so that the file is only read and parsed once per
    process. Subsequent calls return the in-memory list.

    Args:
        input_file (Path): Path to the cleaned Peterson JSON file.

    Returns:
        List[Dict]: List of university records loaded from the JSON.
    """
    try:
        with open(input_file, encoding="utf-8") as f:
            universities = json.load(f)
        logger.info(
            f"Successfully loaded {len(universities)} universities from {input_file}"
        )
        return universities

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {input_file}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading {input_file}: {e}")
        sys.exit(1)


def lookup_university_by_id(unique_id: str, mapping_file: Path = None) -> Dict:
    """
    Look up university data by its unique identifier.

    Uses the cached load_peterson_data() to avoid re-reading the JSON on each call,
    and consults the ID mapping file to find the proper index.

    Args:
        unique_id (str): The unique identifier of the university.
        mapping_file (Path, optional): Path to the ID mapping JSON. If omitted,
            defaults to `<PROJECT_ROOT>/data/chatbot/peterson_data/id_mapping.json`.

    Returns:
        Dict: The university data dictionary, or an empty dict if not found.
    """
    if mapping_file is None:
        mapping_file = (
            PROJECT_ROOT / "data" / "chatbot" / "peterson_data" / "id_mapping.json"
        )

    try:
        id_mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Couldn't load ID mapping: {e}")
        return {}

    if unique_id not in id_mapping:
        logger.warning(f"Unique ID '{unique_id}' not found in mapping")
        return {}

    json_index = id_mapping[unique_id]["json_index"]
    universities = load_peterson_data(
        PROJECT_ROOT / "data" / "cleaned" / "peterson_data.json"
    )

    if 0 <= json_index < len(universities):
        return universities[json_index]
    else:
        logger.error(f"Invalid JSON index {json_index} for unique ID '{unique_id}'")
        return {}


if __name__ == "__main__":
    main()
