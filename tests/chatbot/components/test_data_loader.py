import os
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch


def get_git_root():
    """Get the root directory of the git repository"""
    try:
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .strip()
            .decode("utf-8")
        )
        return Path(git_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Get the project root using git
PROJECT_ROOT = get_git_root()
if PROJECT_ROOT is None:
    print("Error: Not in a git repository or git not found")
    sys.exit(1)

# Change to project root and add to Python path
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from chatbot.components.data_loader import (
    extract_document_id_from_content,
    get_document_ids_from_markdown,
    load_university_documents,
)
from tests.test_logger import (
    log_metrics,
    log_test_result,
    log_test_step,
    setup_test_logger,
)


class TestExtractDocumentId(unittest.TestCase):
    """Test the document ID extraction function"""

    def setUp(self):
        """Set up test logger"""
        self.logger = setup_test_logger("data_loader_extract_id")
        self.logger.info("Starting document ID extraction tests")

    def tearDown(self):
        """Clean up after tests"""
        self.logger.info("Document ID extraction tests cleanup completed")

    def test_extract_valid_document_id(self):
        """Test extracting a valid Document ID from markdown content"""
        test_start_time = datetime.now()

        try:
            log_test_step(self.logger, 1, "Testing extraction of valid Document ID")

            content = """# University Name

**Document ID:** `abc123def456`

## General Information
Some content here.
"""
            result = extract_document_id_from_content(content)
            self.assertEqual(result, "abc123def456")
            self.logger.info(f"Successfully extracted Document ID: {result}")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "document_id_extracted": result,
                "content_length": len(content),
                "test_duration_seconds": round(test_duration, 3),
                "extraction_successful": True,
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_valid_document_id",
                True,
                "Valid Document ID extracted successfully",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "extract_valid_document_id", False, str(e))
            raise

    def test_extract_document_id_with_spaces(self):
        """Test extracting Document ID with spaces around it"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger,
                1,
                "Testing extraction of Document ID with surrounding spaces",
            )

            content = """# University Name

**Document ID:**   `  xyz789  `

## General Information
"""
            result = extract_document_id_from_content(content)
            self.assertEqual(result, "xyz789")
            self.logger.info(f"Successfully extracted trimmed Document ID: {result}")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "document_id_extracted": result,
                "content_length": len(content),
                "test_duration_seconds": round(test_duration, 3),
                "extraction_successful": True,
                "spaces_handled": True,
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_document_id_with_spaces",
                True,
                "Document ID with spaces handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(
                self.logger, "extract_document_id_with_spaces", False, str(e)
            )
            raise

    def test_extract_document_id_not_found(self):
        """Test when no Document ID is present"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Testing extraction when no Document ID is present"
            )

            content = """# University Name

## General Information
Some content without document ID.
"""
            result = extract_document_id_from_content(content)
            self.assertEqual(result, "")
            self.logger.info("Correctly returned empty string for missing Document ID")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "document_id_extracted": result,
                "content_length": len(content),
                "test_duration_seconds": round(test_duration, 3),
                "extraction_successful": True,
                "document_id_missing": True,
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_document_id_not_found",
                True,
                "Missing Document ID handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "extract_document_id_not_found", False, str(e))
            raise

    def test_extract_document_id_malformed(self):
        """Test with malformed Document ID pattern"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Testing extraction with malformed Document ID pattern"
            )

            content = """# University Name

**Document ID:** abc123def456 (missing backticks)

## General Information
"""
            result = extract_document_id_from_content(content)
            self.assertEqual(result, "")
            self.logger.info(
                "Correctly returned empty string for malformed Document ID"
            )

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "document_id_extracted": result,
                "content_length": len(content),
                "test_duration_seconds": round(test_duration, 3),
                "extraction_successful": True,
                "malformed_pattern": True,
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_document_id_malformed",
                True,
                "Malformed Document ID pattern handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "extract_document_id_malformed", False, str(e))
            raise


class TestDataLoader(unittest.TestCase):
    """Test the main data loader functionality"""

    def setUp(self):
        """Set up test logger"""
        self.logger = setup_test_logger("data_loader_main")
        self.logger.info("Starting main data loader tests")

    def tearDown(self):
        """Clean up after tests"""
        self.logger.info("Main data loader tests cleanup completed")

    @patch("chatbot.components.data_loader.DirectoryLoader")
    @patch("chatbot.components.data_loader.lookup_university_by_id")
    @patch("chatbot.components.data_loader.extract_metadata_from_json")
    def test_load_university_documents_success(
        self, mock_extract_meta, mock_lookup, mock_directory_loader
    ):
        """Test successful loading of university documents"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Setting up mock data for successful document loading"
            )

            # Mock markdown document
            mock_doc = Mock()
            mock_doc.page_content = """# Test University

**Document ID:** `test123`

## General Information
Test content
"""
            mock_doc.metadata = {"source": "/path/to/test.md"}

            # Mock DirectoryLoader
            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [mock_doc]
            mock_directory_loader.return_value = mock_loader_instance

            # Mock lookup_university_by_id
            mock_lookup.return_value = {
                "university_name": "Test University",
                "location_contact": {"address": {"city": "Test City"}},
            }

            # Mock extract_metadata_from_json
            mock_extract_meta.return_value = {
                "university_name": "Test University",
                "city": "Test City",
            }

            self.logger.info("Mock setup completed")

            log_test_step(self.logger, 2, "Loading university documents")

            # Call the function
            result = load_university_documents()
            self.logger.info(f"Loaded {len(result)} documents")

            log_test_step(self.logger, 3, "Validating loaded document structure")

            # Assertions
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].metadata["document_id"], "test123")
            self.assertEqual(result[0].metadata["university_name"], "Test University")
            self.assertEqual(result[0].metadata["city"], "Test City")

            self.logger.info("Document structure validation successful")

            log_test_step(self.logger, 4, "Verifying function calls")

            # Verify function calls
            mock_lookup.assert_called_once_with("test123")
            mock_extract_meta.assert_called_once()

            self.logger.info("Function call verification successful")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "documents_loaded": len(result),
                "document_id_found": "test123",
                "metadata_fields_added": len(result[0].metadata),
                "lookup_calls": mock_lookup.call_count,
                "extract_meta_calls": mock_extract_meta.call_count,
                "test_duration_seconds": round(test_duration, 3),
                "test_type": "successful_loading",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "load_university_documents_success",
                True,
                "Document loading with metadata enrichment successful",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(
                self.logger, "load_university_documents_success", False, str(e)
            )
            raise

    @patch("chatbot.components.data_loader.DirectoryLoader")
    @patch("chatbot.components.data_loader.lookup_university_by_id")
    def test_load_university_documents_no_json_record(
        self, mock_lookup, mock_directory_loader
    ):
        """Test loading when no JSON record is found for Document ID"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Setting up mock data for no JSON record scenario"
            )

            # Mock markdown document
            mock_doc = Mock()
            mock_doc.page_content = """# Test University

**Document ID:** `nonexistent123`

## General Information
"""
            mock_doc.metadata = {"source": "/path/to/test.md"}

            # Mock DirectoryLoader
            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [mock_doc]
            mock_directory_loader.return_value = mock_loader_instance

            # Mock lookup returns empty dict (no record found)
            mock_lookup.return_value = {}

            self.logger.info("Mock setup for no JSON record completed")

            log_test_step(
                self.logger, 2, "Loading documents with non-existent Document ID"
            )

            # Call the function
            result = load_university_documents()
            self.logger.info(
                f"Loaded {len(result)} documents despite missing JSON record"
            )

            log_test_step(
                self.logger, 3, "Validating document handling without JSON record"
            )

            # Assertions
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].metadata["document_id"], "nonexistent123")
            # Should still include the document but with minimal metadata

            self.logger.info("Document without JSON record handled correctly")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "documents_loaded": len(result),
                "document_id_found": "nonexistent123",
                "json_record_found": False,
                "lookup_calls": mock_lookup.call_count,
                "test_duration_seconds": round(test_duration, 3),
                "test_type": "no_json_record",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "load_university_documents_no_json_record",
                True,
                "Document loading without JSON record handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(
                self.logger, "load_university_documents_no_json_record", False, str(e)
            )
            raise

    @patch("chatbot.components.data_loader.DirectoryLoader")
    def test_load_university_documents_no_document_id(self, mock_directory_loader):
        """Test loading when markdown has no Document ID"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Setting up mock data for no Document ID scenario"
            )

            # Mock markdown document without Document ID
            mock_doc = Mock()
            mock_doc.page_content = """# Test University

## General Information
No document ID here
"""
            mock_doc.metadata = {"source": "/path/to/test.md"}

            # Mock DirectoryLoader
            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [mock_doc]
            mock_directory_loader.return_value = mock_loader_instance

            self.logger.info("Mock setup for no Document ID completed")

            log_test_step(self.logger, 2, "Loading documents without Document ID")

            # Call the function
            result = load_university_documents()
            self.logger.info(f"Loaded {len(result)} documents without Document ID")

            log_test_step(
                self.logger, 3, "Validating document handling without Document ID"
            )

            # Assertions
            self.assertEqual(len(result), 1)
            # Should still include the document

            self.logger.info("Document without Document ID handled correctly")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "documents_loaded": len(result),
                "document_id_found": False,
                "test_duration_seconds": round(test_duration, 3),
                "test_type": "no_document_id",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "load_university_documents_no_document_id",
                True,
                "Document loading without Document ID handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(
                self.logger, "load_university_documents_no_document_id", False, str(e)
            )
            raise


class TestValidationFunctions(unittest.TestCase):
    """Test the validation and debugging functions"""

    def setUp(self):
        """Set up test logger"""
        self.logger = setup_test_logger("data_loader_validation")
        self.logger.info("Starting validation function tests")

    def tearDown(self):
        """Clean up after tests"""
        self.logger.info("Validation function tests cleanup completed")

    @patch("chatbot.components.data_loader.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_document_ids_from_markdown(self, mock_file, mock_path):
        """Test extracting Document IDs from markdown files"""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger,
                1,
                "Setting up mock markdown files for Document ID extraction",
            )

            # Mock Path.glob to return test files
            mock_md_file1 = Mock()
            mock_md_file1.name = "test1.md"
            mock_md_file2 = Mock()
            mock_md_file2.name = "test2.md"

            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.glob.return_value = [mock_md_file1, mock_md_file2]
            mock_path.return_value = mock_path_instance

            # Mock file content
            file_contents = [
                """# University 1
**Document ID:** `id123`
Content""",
                """# University 2
No document ID here""",
            ]

            mock_file.side_effect = [
                mock_open(read_data=file_contents[0]).return_value,
                mock_open(read_data=file_contents[1]).return_value,
            ]

            self.logger.info("Mock markdown files setup completed")

            log_test_step(self.logger, 2, "Extracting Document IDs from markdown files")

            # Call the function
            result = get_document_ids_from_markdown()
            self.logger.info(f"Processed {len(result)} markdown files")

            log_test_step(self.logger, 3, "Validating Document ID extraction results")

            # Assertions
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["filename"], "test1.md")
            self.assertEqual(result[0]["document_id"], "id123")
            self.assertEqual(result[1]["filename"], "test2.md")
            self.assertEqual(result[1]["document_id"], "NOT_FOUND")

            ids_found = sum(1 for r in result if r["document_id"] != "NOT_FOUND")
            self.logger.info(
                f"Successfully extracted {ids_found} Document IDs from {len(result)} files"
            )

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "markdown_files_processed": len(result),
                "document_ids_found": ids_found,
                "files_without_ids": len(result) - ids_found,
                "test_duration_seconds": round(test_duration, 3),
                "test_type": "document_id_extraction",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "get_document_ids_from_markdown",
                True,
                "Document ID extraction from markdown successful",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(
                self.logger, "get_document_ids_from_markdown", False, str(e)
            )
            raise


if __name__ == "__main__":
    unittest.main()
