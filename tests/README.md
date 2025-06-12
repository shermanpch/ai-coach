# Tests

This directory contains test cases for the CSE-6748 project.

## Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest configuration
├── README.md                      # This file
├── run_tests.py                   # Test runner script
└── chatbot/
    ├── __init__.py
    └── utils/
        ├── __init__.py
        └── test_metadata_extractor.py  # Tests for metadata extraction
```

## Running Tests

### Using unittest (built-in)

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.chatbot.utils.test_metadata_extractor

# Run with verbose output
python -m unittest discover tests -v
```

### Using pytest (if available)

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/chatbot/utils/test_metadata_extractor.py

# Run with verbose output
pytest tests/ -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=chatbot
```

### Using the test runner script

```bash
python tests/run_tests.py
```

## Test Coverage

The current test suite covers:

### `test_metadata_extractor.py`
- Complete metadata extraction from full university data
- Partial metadata extraction with missing fields
- Handling of None values and empty data
- SAT score extraction and parsing
- Majors extraction from multiple categories
- Faculty ratio parsing
- Metadata validation with valid and invalid data
- Integration test with real Abraham Baldwin Agricultural College data

## Adding New Tests

When adding new tests:

1. Create test files following the naming convention `test_*.py`
2. Place them in the appropriate subdirectory matching the module structure
3. Import the modules being tested using the project root path setup in `conftest.py`
4. Use descriptive test method names starting with `test_`
5. Include docstrings explaining what each test verifies

## Test Data

Test cases use a mix of:
- Synthetic data designed to test specific scenarios
- Real university data examples (like Abraham Baldwin Agricultural College)
- Edge cases and error conditions
