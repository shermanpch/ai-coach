# EDA Profiling Reports Generator

This script generates comprehensive HTML profiling reports for CSV files using `ydata_profiling`. The script uses multiprocessing to parallelize the report generation and speed up the process.

## Features

- **Flexible Data Sources**: Process data from either internal or external sources using command-line flags
- **Parallel Processing**: Uses multiprocessing to generate reports for multiple CSV files simultaneously
- **Encoding Fallback**: Automatically tries latin-1 encoding if UTF-8 fails (handles start byte errors)
- **Skip Existing Reports**: Automatically skips files that already have generated reports
- **Comprehensive Logging**: Detailed logging to track progress and identify any issues
- **Error Handling**: Robust error handling to continue processing even if some files fail
- **Performance Monitoring**: Tracks processing time for each file and provides summary statistics
- **Organized Output**: Saves reports to separate directories based on data source

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The script requires either the `--internal` or `--external` flag to specify the data source:

### For Internal Data
Process CSV files from `data/internal/` and save reports to `eda/internal_reports/`:
```bash
python eda/generate_profiling_reports.py --internal
```

### For External Data
Process CSV files from `data/external/` and save reports to `eda/external_reports/`:
```bash
python eda/generate_profiling_reports.py --external
```

### Help
To see all available options:
```bash
python eda/generate_profiling_reports.py --help
```

## Directory Structure

```
project/
├── data/
│   ├── internal/          # Internal CSV files
│   └── external/          # External CSV files
└── eda/
    ├── internal_reports/  # Reports for internal data
    ├── external_reports/  # Reports for external data
    └── generate_profiling_reports.py
```

## Output

- **Internal Data**: HTML reports will be saved in `eda/internal_reports/` with the naming convention: `{original_filename}_profile_report.html`
- **External Data**: HTML reports will be saved in `eda/external_reports/` with the naming convention: `{original_filename}_profile_report.html`
- A log file `profiling_reports.log` will be created in the `eda` folder with detailed processing information
- Console output will show real-time progress

## Configuration

You can modify the following settings in the script:

- **max_workers**: Number of parallel processes (default: CPU cores - 1)
- **minimal**: Set to `True` in the ProfileReport configuration for faster but less detailed reports
- **explorative**: Set to `False` for basic reports

## Performance Notes

- Large CSV files (>1GB) may take significant time and memory
- The script automatically uses all available CPU cores minus one
- Processing time varies based on file size and data complexity
- Memory usage scales with the largest CSV file being processed

## Troubleshooting

- If you encounter memory issues with very large files, consider:
  - Setting `minimal=True` in the ProfileReport configuration
  - Reducing the number of workers
  - Processing files individually for the largest ones

- Check the log file for detailed error messages if any files fail to process

- Ensure the source data directories exist:
  - `data/internal/` for `--internal` flag
  - `data/external/` for `--external` flag

## Examples

```bash
# Generate reports for all CSV files in data/internal/
python eda/generate_profiling_reports.py --internal

# Generate reports for all CSV files in data/external/
python eda/generate_profiling_reports.py --external
```
