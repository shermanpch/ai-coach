# Data Scripts

This directory contains organized scripts for comprehensive data collection, processing, and preparation workflows.

## 📁 Directory Structure

### 📥 [scraper/](scraper/)
**Data Collection & Web Scraping**
- **Georgia Education Data**: Download education data from GOSA (Governor's Office of Student Achievement)
- **Peterson University Data**: Complete pipeline for scraping and processing university information from Peterson's website
- Automated data discovery, batch processing, validation, and error recovery
- Support for selective downloads, URL validation, and comprehensive logging

### 🎯 [sampler/](sampler/)
**Data Sampling & Testing**
- Create manageable sample datasets from large CSV files for development and testing
- Smart sampling (500 rows or 500MB limit) with parallel processing
- Automatic file size analysis and encoding fallback
- Preserves small files and samples large ones intelligently

### 🔄 [preprocessing/](preprocessing/)
**Data Format Conversion**
- Convert Excel files (.xls/.xlsx) to CSV format in-place
- Extract and process Excel files from ZIP archives
- Multi-sheet support with automatic naming conventions
- Multiprocessing for efficient batch conversion

## 🚀 Quick Start Guide

### 1. Data Collection

**List available Georgia education categories:**
```bash
python data/scripts/scraper/georgia_education_data/list_categories.py
```

**Download specific Georgia education data:**
```bash
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --categories "ACT Scores" --years "2023-24"
```

**Download all available Georgia data:**
```bash
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py
```

**Process Peterson university data (complete pipeline):**
```bash
# 1. Extract URLs
python data/scripts/scraper/peterson_search_data/001_get_peterson_urls.py

# 2. Get correct URLs
python data/scripts/scraper/peterson_search_data/002_get_correct_peterson_url.py

# 3. Batch scrape data
python data/scripts/scraper/peterson_search_data/003_get_peterson_data.py --num-batches 10

# 4. Re-scrape failed URLs (if needed)
python data/scripts/scraper/peterson_search_data/004_rescrape_failed_urls.py

# 5. Scrape course information using BeautifulSoup
python data/scripts/scraper/peterson_search_data/005_scrape_courses_bs.py

# 6. Combine course data
python data/scripts/scraper/peterson_search_data/006_combine_peterson_courses.py

# 7. Clean and combine data
python data/scripts/scraper/peterson_search_data/007_clean_peterson_data.py
```

### 2. Data Preprocessing

**Convert Excel files to CSV:**
```bash
# Convert external data
python data/scripts/preprocessing/convert_excel_to_csv.py --external

# Convert internal data
python data/scripts/preprocessing/convert_excel_to_csv.py --internal

# Convert both directories
python data/scripts/preprocessing/convert_excel_to_csv.py --both
```

### 3. Create Sample Datasets

**Sample external data for testing:**
```bash
python data/scripts/sampler/create_sample_data.py --external
```

**Sample internal data for development:**
```bash
python data/scripts/sampler/create_sample_data.py --internal
```

## 📦 Installation

Each directory has its own requirements file. Install dependencies as needed:

```bash
# For data scraping
pip install -r data/scripts/scraper/requirements.txt

# For data sampling
pip install -r data/scripts/sampler/requirements.txt

# For data preprocessing
pip install -r data/scripts/preprocessing/requirements.txt
```

## 📊 Data Organization

### Input Data Structure
```
data/
├── external/          # External data sources (Georgia education, etc.)
├── internal/          # Internal/proprietary data
└── cleaned/           # Processed and cleaned datasets
```

### Output Data Structure
```
data/
├── external/
│   ├── act_scores/
│   │   └── 2023-24/
│   │       └── ACT_2023-24_*.csv
│   ├── peterson_data/
│   │   └── *.json                    # Raw scraped university data
│   └── ...
├── sample_external/   # Sampled external data (≤500 rows)
├── sample_internal/   # Sampled internal data (≤500 rows)

└── cleaned/
    ├── peterson_university_urls.json           # University search results
    ├── peterson_university_urls_backup.json    # Backup of university URLs
    ├── peterson_url_validation_results.json    # URL validation results
    ├── peterson_url_validation_results_backup.json # Backup of validation results
    └── peterson_data.json                      # Final cleaned university dataset
```

## 🔧 Advanced Usage

### Georgia Education Data Scraper
- **Dry run mode**: Preview downloads without downloading
- **Selective downloads**: Filter by categories and years
- **Resume capability**: Skip existing files on re-run
- **Comprehensive logging**: Track all download activities

### Peterson University Scraper
- **Complete pipeline**: URL discovery, validation, batch scraping, and data cleaning
- **Batch processing**: Efficient parallel scraping using Firecrawl API
- **URL validation**: Smart matching against existing university datasets
- **Error recovery**: Automatic re-scraping of failed URLs
- **Structured data**: Comprehensive university information extraction

### Data Sampling
- **Smart size detection**: Automatically determine if sampling is needed
- **Memory-aware**: Prevents memory overflow with large files
- **Parallel processing**: Use all available CPU cores
- **Encoding resilience**: Fallback encoding support

### Excel Conversion
- **In-place conversion**: CSV files created alongside originals
- **Multi-sheet support**: Separate CSV for each Excel sheet
- **ZIP extraction**: Process Excel files within ZIP archives
- **Batch processing**: Handle entire directories efficiently

## 📝 Logging & Monitoring

All scripts provide comprehensive logging in the `logs/` directory:
- **Georgia scraper**: `logs/georgia_data_download.log`
- **Peterson scraper**: `logs/peterson_scraper.log`
- **Sampler**: `logs/sample_data_creation.log`
- **Preprocessing**: `logs/excel_to_csv_conversion.log`

## 🛠️ Troubleshooting

### Common Issues
1. **Network errors**: Check internet connection; scrapers have retry logic
2. **Memory issues**: Use sampling for large datasets
3. **File permissions**: Ensure write access to output directories
4. **Encoding errors**: Scripts include automatic encoding fallback

### Performance Tips
1. **Use sampling**: Create sample datasets for development
2. **Batch processing**: Download/process in smaller batches for large datasets
3. **Parallel processing**: All scripts use multiprocessing where applicable
4. **Resume capability**: Re-run scripts to continue interrupted operations

## 📚 Detailed Documentation

For comprehensive documentation on each component, see the README.md files in each subdirectory:
- [Scraper Documentation](scraper/README.md)
- [Sampler Documentation](sampler/README.md)
- [Preprocessing Documentation](preprocessing/README.md)

## 🎯 Typical Workflow

1. **Collect Data**: Use scrapers to download raw data
2. **Convert Formats**: Convert Excel files to CSV using preprocessing
3. **Create Samples**: Generate sample datasets for development
4. **Process & Analyze**: Use the sample data for model development and testing
5. **Scale Up**: Apply final processing to full datasets when ready
