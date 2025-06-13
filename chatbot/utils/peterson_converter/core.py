"""
Core conversion logic for Peterson university data to Markdown conversion.

This module contains the main conversion functions that orchestrate the
generation of markdown files from Peterson university data.
"""

import json
import os
import shutil
import sys

from dotenv import load_dotenv

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

from .data_utils import generate_unique_id, load_peterson_data
from .formatters import slugify
from .sections import (
    generate_academics_section,
    generate_admissions_section,
    generate_athletics_section,
    generate_campus_life_section,
    generate_data_completeness_section,
    generate_general_info_section,
    generate_tuition_section,
)

load_dotenv()

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def convert_to_markdown():
    """Convert all Peterson university data to individual Markdown files"""
    logger.info("Starting Peterson data to Markdown conversion...")

    # Define file paths relative to project root
    input_file = PROJECT_ROOT / "data" / "cleaned" / "peterson_data.json"
    output_dir = PROJECT_ROOT / "data" / "chatbot" / "peterson_documents"
    chatbot_data_dir = PROJECT_ROOT / "data" / "chatbot"
    mapping_file = output_dir / "id_mapping.json"
    copied_json_file = chatbot_data_dir / "peterson_data.json"

    # Validate input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    # Clear and recreate output directory
    if output_dir.exists():
        logger.info(f"Clearing existing output directory: {output_dir}")
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created fresh output directory: {output_dir}")

    # Ensure chatbot data directory exists
    chatbot_data_dir.mkdir(parents=True, exist_ok=True)

    # Copy peterson_data.json to data/chatbot directory
    try:
        shutil.copy2(input_file, copied_json_file)
        logger.info(f"Copied peterson_data.json to: {copied_json_file}")
    except Exception as e:
        logger.error(f"Failed to copy peterson_data.json: {e}")
        sys.exit(1)

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

            # Generate filename with document ID appended
            filename = slugify(university_name) + f"_{unique_id}.md"
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

            # Generate sections using the modular section generators
            markdown_content.extend(generate_general_info_section(uni_data))
            markdown_content.extend(generate_academics_section(uni_data))
            markdown_content.extend(
                generate_admissions_section(uni_data, university_name)
            )
            markdown_content.extend(generate_tuition_section(uni_data))
            markdown_content.extend(generate_campus_life_section(uni_data))
            markdown_content.extend(generate_athletics_section(uni_data))
            markdown_content.extend(generate_data_completeness_section(uni_data))

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
    logger.info(f"  Copied JSON file: {copied_json_file}")


def main():
    """Main function to orchestrate the Peterson data to Markdown conversion"""
    logger.info("Peterson Data to Markdown Converter - Starting...")

    convert_to_markdown()

    logger.info("Peterson Data to Markdown Converter - Complete!")
