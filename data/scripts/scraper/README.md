# Data Scrapers

This directory contains comprehensive scripts for downloading and scraping various education-related data sources with automated discovery, retry logic, and organized storage.

## 🔧 Scrapers Overview

### 📊 [georgia_education_data/](georgia_education_data/)
**Georgia Education Data Collection**
Scripts for downloading comprehensive Georgia education data from the GOSA (Governor's Office of Student Achievement) website.

**Main Scripts:**
- `download_georgia_education_data.py` - Downloads Georgia education data organized by category and year
- `list_categories.py` - Lists all available data categories from the GOSA website

**Key Features:**
- 🔍 **Automatic Discovery**: Dynamically discovers all available data categories and years
- 📁 **Organized Storage**: Files stored by category and year with timestamped filenames
- 🎯 **Selective Downloads**: Filter downloads by specific categories or years
- 🔄 **Retry Logic**: Exponential backoff for handling network issues
- 🧪 **Dry Run Mode**: Preview downloads without actually downloading files
- 📝 **Comprehensive Logging**: Detailed logging with progress tracking
- ⚡ **Resume Capability**: Skip existing files to resume interrupted downloads

### 🏫 [peterson_search_data/](peterson_search_data/)
**University Data Scraping & Processing**
Complete pipeline for scraping and processing comprehensive university data from Peterson's college search website.

**Main Scripts:**
- `001_get_peterson_urls.py` - Searches Peterson's website for universities and extracts profile URLs
- `002_get_correct_peterson_url.py` - Validates and matches Peterson URLs against university datasets
- `003_get_peterson_data.py` - Batch scrapes university data using Firecrawl API
- `004_rescrape_failed_urls.py` - Re-scrapes URLs that failed initial processing
- `005_scrape_courses_bs.py` - Scrapes course information for universities using BeautifulSoup
- `006_combine_peterson_courses.py` - Combines course data from multiple sources
- `007_clean_peterson_data.py` - Extracts and combines JSON data from scraped files
- `models.py` - Pydantic models defining the data structure for university information

**Key Features:**
- 🔍 **URL Discovery**: Automated search and extraction of university profile URLs
- ✅ **URL Validation**: Smart matching and validation against existing university datasets
- 🌐 **Batch Scraping**: Efficient batch processing using Firecrawl API with retry logic
- 📊 **Structured Data**: Comprehensive university information extraction including:
  - 📍 Location and contact information
  - 🎓 Academic programs and majors
  - 📈 Admission statistics and requirements
  - 💰 Tuition, fees, and financial aid information
  - 🏃 Athletics and campus life details
  - 👨‍🏫 Faculty information and statistics
- 🔄 **Error Recovery**: Automatic identification and re-scraping of failed URLs
- 🧹 **Data Cleaning**: Automated extraction and combination of university data
- 🌐 **Multiple Scraping Methods**: BeautifulSoup-based scraping for reliable course data extraction
- 📝 **Comprehensive Logging**: Detailed progress tracking and error reporting

## 🚀 Installation & Setup

Install the required dependencies:
```bash
pip install -r data/scripts/scraper/requirements.txt
```

**Key Dependencies:**
- `requests` - HTTP requests and web scraping
- `beautifulsoup4` - HTML parsing
- `selenium` - JavaScript-heavy page handling
- `pydantic` - Data validation and modeling
- `pandas` - Data manipulation and CSV handling

## 📖 Quick Start Guide

### Georgia Education Data

**1. Explore Available Data:**
```bash
python data/scripts/scraper/georgia_education_data/list_categories.py
```

**2. Download Specific Categories:**
```bash
# Download ACT scores for 2023-24
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --categories "ACT Scores" --years "2023-24"

# Download multiple categories
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --categories "ACT Scores,SAT Scores" --years "2023-24,2022-23"
```

**3. Download All Available Data:**
```bash
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py
```

**4. Preview Downloads (Dry Run):**
```bash
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --dry-run
```

### Peterson University Data

**Complete Pipeline Process:**

**1. Extract University URLs:**
```bash
python data/scripts/scraper/peterson_search_data/001_get_peterson_urls.py
```

**2. Validate URLs Against Dataset:**
```bash
python data/scripts/scraper/peterson_search_data/002_get_correct_peterson_url.py
```

**3. Batch Scrape University Data:**
```bash
python data/scripts/scraper/peterson_search_data/003_get_peterson_data.py --num-batches 10
```

**4. Re-scrape Failed URLs (if needed):**
```bash
python data/scripts/scraper/peterson_search_data/004_rescrape_failed_urls.py
```

**5. Scrape Course Information:**
```bash
python data/scripts/scraper/peterson_search_data/005_scrape_courses_bs.py
```

**6. Combine Course Data:**
```bash
python data/scripts/scraper/peterson_search_data/006_combine_peterson_courses.py
```

**7. Clean and Combine Data:**
```bash
python data/scripts/scraper/peterson_search_data/007_clean_peterson_data.py
```

**Pipeline Overview:**
1. **URL Discovery**: Searches Peterson's website for university URLs
2. **URL Correction**: Validates and gets correct URLs against existing university datasets
3. **Batch Scraping**: Uses Firecrawl API to scrape university data in batches
4. **Error Recovery**: Identifies and re-scrapes any failed URLs
5. **Course Scraping**: Scrapes detailed course information for universities
6. **Course Combination**: Combines course data from multiple sources
7. **Data Cleaning**: Extracts JSON data and combines into single dataset

## 📁 Data Organization & Output

### Georgia Education Data Structure
```
data/external/
├── act_scores/
│   ├── 2023-24/
│   │   └── ACT_2023-24_Highest_2025-01-14_16_21_13.csv
│   ├── 2022-23/
│   │   └── ACT_2022-23_Highest_2025-01-14_16_22_45.csv
│   └── ...
├── advanced_placement_ap_scores/
│   ├── 2023-24/
│   │   └── AP_2023-24_2025-01-15_15_03_20.csv
│   └── ...
├── georgia_milestones_assessments/
├── enrollment_data/
├── graduation_rates/
├── financial_data/
└── ...
```

### Peterson University Data Structure
```
data/
├── cleaned/
│   ├── peterson_university_urls.json           # University search results and URLs
│   ├── peterson_university_urls_backup.json    # Backup of university URLs
│   ├── peterson_url_validation_results.json    # URL validation and matching results
│   ├── peterson_url_validation_results_backup.json # Backup of validation results
│   └── peterson_data.json                      # Final cleaned university dataset

└── external/
    ├── peterson_data/
    │   └── *.json                              # Raw scraped university data files
    └── peterson_courses_data/
        └── *.json                              # Course data scraped using BeautifulSoup
```

## 📊 Available Data Categories (Georgia)

The Georgia scraper automatically discovers all available categories from the GOSA website. Common categories include:

**Academic Performance:**
- ACT Scores, SAT Scores, AP Scores
- Georgia Milestones Assessments (EOG, EOC)
- NAEP (National Assessment of Educational Progress)

**Student Demographics & Enrollment:**
- Enrollment by Grade, Race, Gender
- English Learners, Students with Disabilities
- Free and Reduced Lunch Eligibility

**School Performance Metrics:**
- Attendance Rates, Graduation Rates
- Dropout Rates, Student Mobility Rates
- College and Career Readiness

**Financial & Personnel Data:**
- School Revenues and Expenditures
- Personnel Counts and Salaries
- Educator Qualifications and Experience

**Infrastructure & Resources:**
- Facilities and Technology
- Class Sizes and Student-Teacher Ratios

## 🔧 Advanced Usage & Configuration

### Georgia Education Data Scraper

**Command Line Options:**
```bash
python download_georgia_education_data.py [OPTIONS]

Options:
  --categories TEXT    Comma-separated list of categories to download
  --years TEXT        Comma-separated list of years to download
  --dry-run          Preview downloads without downloading
  --help             Show help message
```

**Configuration Tips:**
- Use exact category names from `list_categories.py`
- Year format: "2023-24", "2022-23", etc.
- Large datasets may take significant time; consider downloading in batches
- Use dry-run mode to estimate download size and time

### Peterson University Scraper

**Pipeline Requirements:**
- University dataset (CSV/JSON) for URL validation
- Firecrawl API key for batch scraping
- Internet connection for web scraping

**Performance Features:**
- **Batch Processing**: Scrapes multiple URLs simultaneously using Firecrawl API
- **Smart Validation**: Matches URLs against existing datasets before scraping
- **Error Recovery**: Automatic identification and re-processing of failed URLs
- **Efficient Storage**: Organized file structure with progress tracking
- **Resume Capability**: Can resume interrupted scraping jobs

## 📝 Logging & Monitoring

### Georgia Education Data
- **Log File**: `logs/georgia_data_download.log`
- **Content**: Download progress, errors, file information, timing statistics
- **Levels**: INFO, WARNING, ERROR with detailed timestamps

### Peterson University Data
- **Log Files**:
  - `logs/peterson_batch_scraper.log` - Batch scraping progress and job submissions
  - `logs/peterson_data_cleaner.log` - Data cleaning and extraction progress
  - `logs/rescrape_failed_urls.log` - Failed URL re-scraping activities
- **Content**: Pipeline progress, URL validation, batch job tracking, data extraction, error recovery
- **Monitoring**: Real-time progress tracking for each pipeline stage

## 🛠️ Troubleshooting Guide

### Common Issues & Solutions

**Network-Related Issues:**
1. **Connection timeouts**: Scripts include retry logic with exponential backoff
2. **Rate limiting**: Appropriate delays built into scrapers
3. **DNS issues**: Check internet connection and DNS settings

**File & Storage Issues:**
1. **Disk space**: Large datasets require significant storage space
2. **File permissions**: Ensure write permissions to output directories
3. **Existing files**: Scripts automatically skip existing files

**Data-Specific Issues:**
1. **Category names**: Use exact names from `list_categories.py`
2. **Year formats**: Follow "YYYY-YY" format (e.g., "2023-24")
3. **Large files**: Some datasets are very large; be patient or use selective downloads

### Performance Optimization

**For Large Downloads:**
1. **Batch processing**: Download categories in smaller batches
2. **Selective downloads**: Focus on specific years or categories
3. **Resume capability**: Re-run scripts to continue interrupted downloads
4. **Storage planning**: Ensure adequate disk space before starting

**For Web Scraping:**
1. **Stable internet**: Ensure reliable internet connection
2. **Browser compatibility**: Keep browser drivers updated for Selenium
3. **Memory management**: Monitor memory usage for large scraping jobs

## 🔍 Data Quality & Validation

### Georgia Education Data
- **Automatic validation**: File size and format checks
- **Timestamp tracking**: All downloads timestamped for version control
- **Duplicate prevention**: Automatic skipping of existing files
- **Error logging**: Comprehensive error tracking and reporting

### Peterson University Data
- **Pipeline validation**: Multi-stage validation throughout the process
- **URL matching**: Smart matching against existing university datasets
- **Data consistency**: Pydantic models ensure structured data extraction
- **Error tracking**: Comprehensive tracking of failed URLs and re-scraping
- **Data completeness**: Final dataset combines all successfully scraped universities

## 📚 Additional Resources

### Getting Help
```bash
# Georgia scraper help
python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --help

# List available categories
python data/scripts/scraper/georgia_education_data/list_categories.py

# Check Peterson pipeline logs
tail -f logs/peterson_batch_scraper.log
tail -f logs/peterson_data_cleaner.log
tail -f logs/rescrape_failed_urls.log

# Check Georgia scraper logs
tail -f logs/georgia_data_download.log
```

### Best Practices
1. **Start small**: Begin with specific categories or years
2. **Monitor progress**: Check logs regularly for large downloads
3. **Plan storage**: Estimate storage requirements before downloading
4. **Backup data**: Consider backing up downloaded data
5. **Respect terms**: Both scrapers respect website terms of service

## ⚠️ Important Notes

- **Terms of Service**: Both scrapers include appropriate delays and respect website terms
- **Data Size**: Some datasets are very large (>1GB); plan accordingly
- **Processing Time**: Large downloads may take hours; use screen/tmux for long sessions
- **Directory Structure**: Scripts automatically create necessary directory structures
- **Error Recovery**: Failed operations are logged and can be retried
- **Browser Requirements**: Peterson scraper requires Chrome/Chromium for Selenium

## 🔄 Updates & Maintenance

- **Regular Updates**: GOSA website structure may change; scripts may need updates
- **Dependency Management**: Keep dependencies updated for security and compatibility
- **Log Rotation**: Consider rotating log files for long-term usage
- **Data Archival**: Plan for long-term storage and archival of downloaded data
