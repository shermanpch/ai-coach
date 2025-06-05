# Georgia Education Data Scraper

This folder contains scripts for downloading Georgia education data from the [GOSA (Governor's Office of Student Achievement) website](https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data).

## Scripts

### 1. download_georgia_education_data.py

Downloads Georgia education data and organizes it by category and year.

#### Features

- **Automatic Data Discovery**: Parses the GOSA website to find all available data download links (CSV, XLS, XLSX, ZIP)
- **Organized Storage**: Downloads files organized by data category and year in the `data/external/` folder
- **Selective Downloads**: Filter by specific data categories or years
- **Retry Logic**: Automatic retry with exponential backoff for failed downloads
- **Dry Run Mode**: Preview what would be downloaded without actually downloading
- **Comprehensive Logging**: Detailed logs of all download activities
- **Skip Existing Files**: Automatically skips files that have already been downloaded
- **Excludes Retired Data**: Automatically excludes retired assessment categories

### 2. list_categories.py

Lists all available data categories from the GOSA website.

## Installation

Install the required dependencies:
```bash
pip install -r data/scripts/scraper/requirements.txt
```

## Usage

### List Available Categories
First, see what data categories are available:
```bash
python data/scripts/scraper/list_categories.py
```

### Download Data

**Download all available data:**
```bash
python data/scripts/scraper/download_georgia_education_data.py
```

**Download specific categories:**
```bash
python data/scripts/scraper/download_georgia_education_data.py --categories "ACT Scores,Advanced Placement (AP) Scores"
```

**Download specific years:**
```bash
python data/scripts/scraper/download_georgia_education_data.py --years "2023-24,2022-23,2021-22"
```

**Combine filters:**
```bash
python data/scripts/scraper/download_georgia_education_data.py --categories "ACT Scores" --years "2023-24,2022-23"
```

**Dry run to see what would be downloaded:**
```bash
python data/scripts/scraper/download_georgia_education_data.py --dry-run
```

**Custom output directory:**
```bash
python data/scripts/scraper/download_georgia_education_data.py --output-dir "custom/path"
```

## Data Organization

Downloaded files are organized as follows:
```
data/external/
├── act_scores/
│   ├── 2023-24/
│   │   └── ACT_2023-24_Highest_2025-01-14_16_21_13.csv
│   ├── 2022-23/
│   │   └── ACT_2022-23_Highest_2025-01-15_09_21_13.csv
│   └── ...
├── advanced_placement_ap_scores/
│   ├── 2023-24/
│   │   └── AP_2023-24_2025-01-15_15_03_20.csv
│   └── ...
├── student_mobility_rates_by_district/
│   ├── 2023-24/
│   │   └── 2024_District_Mobility_for_Display.xls
│   └── ...
└── ...
```

## Available Data Categories

The script automatically discovers all available categories from the GOSA website, including:

- ACT Scores, SAT Scores, AP Scores
- Georgia Milestones Assessments (EOG, EOC)
- Enrollment, Attendance, Graduation Rates
- Financial data (Revenues, Expenditures, Salaries)
- Personnel and Educator Qualifications
- English Learners, Dropout Rates
- Student Mobility Rates
- And many more...

Run `python data/scripts/scraper/list_categories.py` to see the complete current list.

## Logging

The download script creates detailed logs in `georgia_data_download.log` including:
- Download progress and status
- File sizes and locations
- Error messages and retry attempts
- Summary statistics

## Tips and Best Practices

### 1. Start with a Dry Run
Always use `--dry-run` first to see what will be downloaded:
```bash
python data/scripts/scraper/download_georgia_education_data.py --categories "ACT Scores" --dry-run
```

### 2. Use Exact Category Names
Category names must match exactly. Use the list script to see exact names:
```bash
python data/scripts/scraper/list_categories.py
```

### 3. Download in Batches
For large downloads, consider downloading in smaller batches:
```bash
# First batch - Assessment data
python data/scripts/scraper/download_georgia_education_data.py --categories "ACT Scores,SAT Scores (Recent),Advanced Placement (AP) Scores"

# Second batch - Enrollment data
python data/scripts/scraper/download_georgia_education_data.py --categories "Enrollment by Grade Level,Enrollment by Subgroup Programs"
```

### 4. Resume Failed Downloads
If some downloads fail, just run the script again - it will skip existing files:
```bash
python data/scripts/scraper/download_georgia_education_data.py --categories "ACT Scores"
# Will skip already downloaded files
```

## Troubleshooting

### Common Issues

1. **Category not found**: Use exact category names from `list_categories.py`
2. **Network errors**: The script has retry logic, but check your internet connection
3. **Permission errors**: Ensure you have write permissions to the output directory
4. **Large downloads**: Some files are very large; be patient or download in smaller batches

### Getting Help
```bash
python data/scripts/scraper/download_georgia_education_data.py --help
```

## Notes

- The download script respects the GOSA website's structure and includes appropriate delays between requests
- Large datasets may take significant time to download
- The script automatically creates the necessary directory structure
- Failed downloads are logged and can be retried by running the script again
- Retired assessment categories are automatically excluded from the main data categories
