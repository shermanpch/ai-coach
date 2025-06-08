# Georgia Education Data Scripts

This folder contains scripts specifically for scraping Georgia education data from the GOSA (Governor's Office of Student Achievement) website.

## Scripts

- **`download_georgia_education_data.py`** - Main script for downloading Georgia education data with parallel processing, retry logic, and anti-detection measures
- **`list_categories.py`** - Utility script to list all available data categories from the GOSA website

## Usage

From the project root directory:

```bash
# List available categories
python data/scripts/scraper/georgia_education_data/list_categories.py

# Download data
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py
```

See the main [scraper README](../README.md) for detailed usage instructions and examples.
