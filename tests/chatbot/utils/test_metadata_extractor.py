# Test cases for the metadata extraction utility

import os
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path


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

from chatbot.utils.metadata_extractor import extract_metadata_from_json
from tests.test_logger import (
    log_metrics,
    log_test_result,
    log_test_step,
    setup_test_logger,
)


class TestMetadataExtractor(unittest.TestCase):
    """Test cases for metadata extraction functionality."""

    def setUp(self):
        """Set up test data for use in test methods."""
        # Set up logger
        self.logger = setup_test_logger("metadata_extractor")

        # Load real university data from the JSON file
        import json

        json_path = PROJECT_ROOT / "data" / "cleaned" / "peterson_data.json"
        self.logger.info(f"Loading university data from: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            all_universities = json.load(f)

        # Use Swarthmore College (first university) as our complete data example
        self.complete_university_data = all_universities[0]
        self.logger.info(
            f"Using {self.complete_university_data['university_name']} as complete data example"
        )

        # Minimal university data for testing edge cases
        self.minimal_university_data = {"university_name": "Test Minimal University"}

        # Partial data for testing missing fields
        self.partial_university_data = {
            "university_name": "Test Partial University",
            "location_contact": {
                "address": {
                    "city": "Test City",
                    "state": "Test State",
                    # Missing zip_code
                }
            },
            "admissions": {
                "applying": {
                    "application_fee": None,  # Explicitly None
                    "avg_high_school_gpa": 3.2,
                }
                # Missing test_scores_accepted
            },
        }

        self.logger.info("Test data setup completed")

    def tearDown(self):
        """Clean up after each test method"""
        self.logger.info("Test cleanup completed")

    def test_extract_complete_metadata(self):
        """Test extraction with complete university data (Swarthmore College)."""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger,
                1,
                "Testing metadata extraction with complete university data",
            )

            metadata = extract_metadata_from_json(self.complete_university_data)
            self.logger.info(f"Extracted {len(metadata)} metadata fields")

            log_test_step(self.logger, 2, "Validating presence of expected fields")

            # Check that key fields are present (removed majors since it's no longer extracted)
            expected_fields = [
                "university_name",
                "city",
                "state",
                "zip_code",
                "application_fee",
                "acceptance_rate",
                "sat_reading_25",
                "sat_reading_75",
                "sat_math_25",
                "sat_math_75",
                "room_and_board",
                "percent_undergrads_in_housing",
                "has_college_housing",
                "total_faculty",
                "student_faculty_ratio",
            ]

            present_fields = 0
            for field in expected_fields:
                self.assertIn(
                    field, metadata, f"Field {field} should be present in metadata"
                )
                present_fields += 1

            self.logger.info(f"Validated {present_fields} expected fields are present")

            log_test_step(self.logger, 3, "Validating specific field values")

            # Check specific values from Swarthmore College
            assertions = [
                ("university_name", "Swarthmore College"),
                ("city", "Swarthmore"),
                ("state", "Pennsylvania"),
                ("zip_code", "19081-1397"),
                ("application_fee", 60),
                ("acceptance_rate", 7),
                ("sat_reading_25", 720),
                ("sat_reading_75", 770),
                ("sat_math_25", 740),
                ("sat_math_75", 790),
                ("room_and_board", 20308),
                ("percent_undergrads_in_housing", 95),
                ("has_college_housing", True),
                ("total_faculty", 236),
                ("student_faculty_ratio", 8),
            ]

            for field, expected_value in assertions:
                self.assertEqual(metadata[field], expected_value)

            self.logger.info(f"Validated {len(assertions)} specific field values")

            # Calculate test duration and log metrics
            test_duration = (datetime.now() - test_start_time).total_seconds()

            test_metrics = {
                "total_metadata_fields": len(metadata),
                "expected_fields_validated": len(expected_fields),
                "specific_values_validated": len(assertions),
                "majors_excluded": True,
                "test_duration_seconds": round(test_duration, 3),
                "university_tested": metadata["university_name"],
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_complete_metadata",
                True,
                "All validations passed for complete data",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "extract_complete_metadata", False, str(e))
            raise

    def test_extract_minimal_metadata(self):
        """Test extraction with minimal university data."""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger,
                1,
                "Testing metadata extraction with minimal university data",
            )

            metadata = extract_metadata_from_json(self.minimal_university_data)

            # Should only have university_name
            self.assertEqual(len(metadata), 1)
            self.assertEqual(metadata["university_name"], "Test Minimal University")

            self.logger.info(
                f"Successfully extracted {len(metadata)} field from minimal data"
            )

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "metadata_fields_extracted": len(metadata),
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "minimal",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_minimal_metadata",
                True,
                "Minimal data extraction successful",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "extract_minimal_metadata", False, str(e))
            raise

    def test_extract_partial_metadata(self):
        """Test extraction with partial university data and None values."""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger,
                1,
                "Testing metadata extraction with partial university data",
            )

            metadata = extract_metadata_from_json(self.partial_university_data)

            log_test_step(self.logger, 2, "Validating present fields")

            # Check present fields
            self.assertEqual(metadata["university_name"], "Test Partial University")
            self.assertEqual(metadata["city"], "Test City")
            self.assertEqual(metadata["state"], "Test State")
            self.assertEqual(metadata["avg_high_school_gpa"], 3.2)

            present_fields = 4
            self.logger.info(f"Validated {present_fields} present fields")

            log_test_step(self.logger, 3, "Validating missing/None fields are excluded")

            # Check that None values and missing fields are not included
            excluded_fields = ["zip_code", "application_fee", "sat_reading_25"]
            for field in excluded_fields:
                self.assertNotIn(field, metadata)

            self.logger.info(
                f"Confirmed {len(excluded_fields)} fields correctly excluded"
            )

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "metadata_fields_extracted": len(metadata),
                "present_fields_validated": present_fields,
                "excluded_fields_validated": len(excluded_fields),
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "partial",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "extract_partial_metadata",
                True,
                "Partial data extraction with proper exclusions",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "extract_partial_metadata", False, str(e))
            raise

    def test_empty_data(self):
        """Test extraction with empty dictionary."""
        test_start_time = datetime.now()

        try:
            log_test_step(self.logger, 1, "Testing metadata extraction with empty data")

            metadata = extract_metadata_from_json({})

            # Should only have university_name as None, which gets filtered out
            self.assertEqual(len(metadata), 0)
            self.logger.info("Successfully handled empty data input")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "metadata_fields_extracted": len(metadata),
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "empty",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger, "empty_data", True, "Empty data handled correctly"
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "empty_data", False, str(e))
            raise

    def test_missing_test_scores(self):
        """Test extraction when test scores section is missing or empty."""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Testing metadata extraction with missing test scores"
            )

            data_no_scores = {
                "university_name": "No Scores University",
                "admissions": {},
            }

            metadata = extract_metadata_from_json(data_no_scores)
            self.assertEqual(metadata["university_name"], "No Scores University")
            self.assertNotIn("sat_reading_25", metadata)
            self.assertNotIn("sat_math_25", metadata)

            self.logger.info("Successfully handled missing test scores data")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "metadata_fields_extracted": len(metadata),
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "missing_test_scores",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "missing_test_scores",
                True,
                "Missing test scores handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "missing_test_scores", False, str(e))
            raise

    def test_partial_test_scores(self):
        """Test extraction when only some test scores are available."""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger, 1, "Testing metadata extraction with partial test scores"
            )

            data_partial_scores = {
                "university_name": "Partial Scores University",
                "admissions": {
                    "test_scores_accepted": [
                        {
                            "test": "SAT Math",
                            "percentile_25": 500,
                            # Missing percentile_75
                        }
                    ]
                },
            }

            metadata = extract_metadata_from_json(data_partial_scores)
            self.assertEqual(metadata["sat_math_25"], 500)
            self.assertNotIn("sat_math_75", metadata)
            self.assertNotIn("sat_reading_25", metadata)

            self.logger.info("Successfully handled partial test scores data")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "metadata_fields_extracted": len(metadata),
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "partial_test_scores",
                "sat_scores_extracted": 1,
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "partial_test_scores",
                True,
                "Partial test scores handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "partial_test_scores", False, str(e))
            raise

    def test_faculty_ratio_parsing(self):
        """Test parsing of student-faculty ratio strings."""
        test_start_time = datetime.now()

        try:
            log_test_step(self.logger, 1, "Testing student-faculty ratio parsing")

            test_cases = [
                ({"student_faculty_ratio": "15:1"}, 15),
                ({"student_faculty_ratio": "20:1"}, 20),
                ({"student_faculty_ratio": "0:1"}, None),  # Should be filtered out
                ({"student_faculty_ratio": "invalid"}, None),
                ({"student_faculty_ratio": ""}, None),
            ]

            successful_parses = 0
            filtered_cases = 0

            for i, (faculty_data, expected_ratio) in enumerate(test_cases, 1):
                log_test_step(
                    self.logger,
                    i + 1,
                    f"Testing ratio case: {faculty_data['student_faculty_ratio']}",
                )

                data = {"university_name": "Test University", "faculty": faculty_data}
                metadata = extract_metadata_from_json(data)

                if expected_ratio is None:
                    self.assertNotIn("student_faculty_ratio", metadata)
                    filtered_cases += 1
                    self.logger.info(
                        f"Correctly filtered invalid ratio: {faculty_data['student_faculty_ratio']}"
                    )
                else:
                    self.assertEqual(metadata["student_faculty_ratio"], expected_ratio)
                    successful_parses += 1
                    self.logger.info(
                        f"Successfully parsed ratio: {faculty_data['student_faculty_ratio']} -> {expected_ratio}"
                    )

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "total_test_cases": len(test_cases),
                "successful_parses": successful_parses,
                "filtered_cases": filtered_cases,
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "faculty_ratio_parsing",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "faculty_ratio_parsing",
                True,
                "All ratio parsing cases handled correctly",
            )

        except Exception as e:
            self.logger.error(f"Test failed with exception: {str(e)}")
            log_test_result(self.logger, "faculty_ratio_parsing", False, str(e))
            raise


class TestMetadataExtractorIntegration(unittest.TestCase):
    """Integration tests using real-world-like data."""

    def setUp(self):
        """Set up test logger for integration tests."""
        self.logger = setup_test_logger("metadata_extractor_integration")
        self.logger.info("Starting integration tests")

    def tearDown(self):
        """Clean up after integration tests."""
        self.logger.info("Integration tests cleanup completed")

    def test_abraham_baldwin_agricultural_college(self):
        """Test with the Abraham Baldwin Agricultural College example from the user."""
        test_start_time = datetime.now()

        try:
            log_test_step(
                self.logger,
                1,
                "Testing integration with Abraham Baldwin Agricultural College data",
            )

            # This is the actual data structure from the user's example
            abac_data = {
                "university_name": "Abraham Baldwin Agricultural College",
                "location_contact": {
                    "address": {
                        "street": "Box 4, 2802 Moore Highway",
                        "city": "Tifton",
                        "state": "Georgia",
                        "zip_code": "31793-2601",
                        "country": "United States",
                    }
                },
                "admissions": {
                    "overall": {
                        "applied": 2618,
                        "accepted": 2020,
                        "enrolled": 3768,
                        "acceptance_rate": 77,
                    },
                    "applying": {"application_fee": 20, "avg_high_school_gpa": 2.85},
                    "test_scores_accepted": [
                        {
                            "test": "SAT Critical Reading",
                            "avg_score": None,
                            "percentile_25": 460,
                            "percentile_75": 570,
                        },
                        {
                            "test": "SAT Math",
                            "avg_score": None,
                            "percentile_25": 430,
                            "percentile_75": 530,
                        },
                    ],
                },
                "tuition_and_fees": {
                    "tuition": [
                        {"category": "In-state", "amount": 2616},
                        {"category": "Out-of-state", "amount": 9936},
                    ],
                    "fees": [{"category": "Room & board", "amount": 9800}],
                },
                "majors_and_degrees": [
                    {
                        "category": "Agriculture, Agriculture Operations, And Related Sciences",
                        "programs": [
                            {"name": "Agricultural Business And Management, General"},
                            {"name": "Agriculture, General"},
                        ],
                    }
                ],
            }

            log_test_step(self.logger, 2, "Extracting metadata from ABAC data")
            metadata = extract_metadata_from_json(abac_data)
            self.logger.info(
                f"Extracted {len(metadata)} metadata fields from ABAC data"
            )

            log_test_step(self.logger, 3, "Validating extracted metadata values")

            # Validate the extraction
            validations = [
                ("university_name", "Abraham Baldwin Agricultural College"),
                ("city", "Tifton"),
                ("state", "Georgia"),
                ("zip_code", "31793-2601"),
                ("application_fee", 20),
                ("avg_high_school_gpa", 2.85),
                ("acceptance_rate", 77),
                ("sat_reading_25", 460),
                ("sat_reading_75", 570),
                ("sat_math_25", 430),
                ("sat_math_75", 530),
                ("tuition_in_state", 2616),
                ("tuition_out_of_state", 9936),
                ("room_and_board", 9800),
            ]

            for field, expected_value in validations:
                self.assertEqual(metadata[field], expected_value)

            self.logger.info(f"Successfully validated {len(validations)} field values")

            test_duration = (datetime.now() - test_start_time).total_seconds()
            test_metrics = {
                "university_tested": "Abraham Baldwin Agricultural College",
                "total_metadata_fields": len(metadata),
                "field_validations": len(validations),
                "test_duration_seconds": round(test_duration, 3),
                "data_type": "integration_real_world",
            }

            log_metrics(self.logger, test_metrics)
            log_test_result(
                self.logger,
                "abraham_baldwin_agricultural_college",
                True,
                "Integration test with real-world data successful",
            )

        except Exception as e:
            self.logger.error(f"Integration test failed with exception: {str(e)}")
            log_test_result(
                self.logger, "abraham_baldwin_agricultural_college", False, str(e)
            )
            raise


if __name__ == "__main__":
    unittest.main()
