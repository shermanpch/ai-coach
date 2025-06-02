# Data Scripts

This directory contains organized scripts for data collection and processing.

## Folders

### 📥 [scraper/](scraper/)
Scripts for downloading Georgia education data from the GOSA website.
- `download_georgia_education_data.py` - Main download script
- `list_categories.py` - List available data categories

### 🎯 [sampler/](sampler/)
Scripts for creating sampled versions of CSV files for testing and development.
- `create_sample_data.py` - Create sampled datasets

### 🔄 [preprocessing/](preprocessing/)
Scripts for data preprocessing and format conversion.
- `convert_excel_to_csv.py` - Convert Excel files (.xls/.xlsx) to CSV format and extract ZIP files

## Quick Start

### Download Data
```bash
# List available categories
python data/scripts/scraper/list_categories.py

# Download specific data
python data/scripts/scraper/download_georgia_education_data.py --categories "ACT Scores" --years "2023-24"
```

### Create Samples
```bash
# Sample external data
python data/scripts/sampler/create_sample_data.py --external

# Sample internal data  
python data/scripts/sampler/create_sample_data.py --internal
```

### Convert Excel to CSV
```bash
# Convert Excel files in external directory
python data/scripts/preprocessing/convert_excel_to_csv.py --external

# Convert Excel files in internal directory
python data/scripts/preprocessing/convert_excel_to_csv.py --internal

# Convert Excel files in both directories
python data/scripts/preprocessing/convert_excel_to_csv.py --both
```

## Installation

Each folder has its own `requirements.txt` file. Install dependencies as needed:

```bash
# For scraper
pip install -r data/scripts/scraper/requirements.txt

# For sampler
pip install -r data/scripts/sampler/requirements.txt

# For preprocessing
pip install -r data/scripts/preprocessing/requirements.txt
```

See the README.md files in each folder for detailed documentation. 