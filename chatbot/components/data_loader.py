import json
import os
import re
from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document

# Original project imports should now work directly because of pip install -e .
from chatbot import config
from chatbot.utils.metadata_extractor import extract_metadata_from_json
from chatbot.utils.peterson_converter import lookup_university_by_id
from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)


def extract_document_id_from_content(content: str) -> str:
    """
    Extract the Document ID from markdown content.

    Args:
        content (str): The markdown content

    Returns:
        str: The extracted document ID, or empty string if not found
    """
    # Look for pattern: **Document ID:** `some_id_here`
    pattern = r"\*\*Document ID:\*\*\s*`([^`]+)`"
    match = re.search(pattern, content)

    if match:
        return match.group(1).strip()

    return ""


def load_university_documents() -> List[Document]:
    """
    Loads markdown documents from the specified directory and enriches them
    with metadata using unique Document IDs for precise matching.
    """
    # Load markdown files using TextLoader
    logger.info(f"Loading markdown files from: {config.MARKDOWN_DATA_DIR}")
    loader = DirectoryLoader(
        path=config.MARKDOWN_DATA_DIR,
        glob="*.md",
        loader_cls=TextLoader,
        show_progress=True,
        use_multithreading=True,
    )
    markdown_docs = loader.load()
    logger.info(f"Loaded {len(markdown_docs)} markdown files")

    processed_docs: List[Document] = []
    matched_count = 0
    unmatched_count = 0

    for md_doc in markdown_docs:
        # Extract Document ID from the markdown content
        document_id = extract_document_id_from_content(md_doc.page_content)

        if document_id:
            # Look up the university data using the unique ID
            json_record = lookup_university_by_id(document_id)

            if json_record:
                # Extract metadata from the JSON record
                extracted_meta = extract_metadata_from_json(json_record)

                # Merge with existing metadata (like 'source')
                md_doc.metadata.update(extracted_meta)

                # Add the document ID to metadata for easy reference
                md_doc.metadata["document_id"] = document_id

                processed_docs.append(md_doc)
                matched_count += 1
            else:
                logger.warning(f"No JSON record found for Document ID: {document_id}")
                # Still add the doc with minimal metadata
                md_doc.metadata["document_id"] = document_id
                processed_docs.append(md_doc)
                unmatched_count += 1
        else:
            # No Document ID found in content
            filename = os.path.basename(md_doc.metadata.get("source", "unknown"))
            logger.warning(f"No Document ID found in file: {filename}")
            processed_docs.append(md_doc)
            unmatched_count += 1

    logger.info(
        f"Successfully loaded and processed {len(processed_docs)} university documents."
    )
    logger.info(f"  - Matched with JSON using Document ID: {matched_count}")
    logger.info(f"  - Unmatched: {unmatched_count}")
    return processed_docs


def get_university_names_from_json() -> List[str]:
    """
    Get all university names from the JSON data for debugging/reference.
    """
    with open(config.JSON_DATA_PATH, encoding="utf-8") as f:
        all_json_data = json.load(f)

    return [record["university_name"] for record in all_json_data]


def get_markdown_filenames() -> List[str]:
    """
    Get all markdown filenames for debugging/reference.
    """
    markdown_dir = Path(config.MARKDOWN_DATA_DIR)
    if not markdown_dir.exists():
        return []

    return [f.name for f in markdown_dir.glob("*.md")]


def get_document_ids_from_markdown() -> List[dict]:
    """
    Extract all Document IDs from markdown files for debugging/reference.

    Returns:
        List[dict]: List of dictionaries with filename and document_id
    """
    markdown_dir = Path(config.MARKDOWN_DATA_DIR)
    if not markdown_dir.exists():
        return []

    document_ids = []

    for md_file in markdown_dir.glob("*.md"):
        try:
            with open(md_file, encoding="utf-8") as f:
                content = f.read()

            document_id = extract_document_id_from_content(content)
            document_ids.append(
                {
                    "filename": md_file.name,
                    "document_id": document_id if document_id else "NOT_FOUND",
                }
            )
        except Exception as e:
            logger.error(f"Error reading {md_file}: {e}")
            document_ids.append({"filename": md_file.name, "document_id": "ERROR"})

    return document_ids
