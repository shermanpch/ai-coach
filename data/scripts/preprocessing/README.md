# Excel to CSV Conversion Script

This script converts Excel files (.xls/.xlsx) to CSV format and extracts ZIP files to process any Excel files contained within them. **CSV files are created in the same directories as the original files.**

## Features

- **Excel Conversion**: Converts .xls and .xlsx files to CSV format in the same directories as the original files
- **Multi-sheet Support**: If an Excel file has multiple sheets, creates separate CSV files named `{filename}_{sheetname}.csv`
- **ZIP Extraction**: Extracts ZIP files to subdirectories and processes any Excel files found within them
- **Multiprocessing**: Uses multiple CPU cores for faster processing
- **In-place Processing**: CSV files are created alongside the original files, maintaining the existing directory structure
- **Comprehensive Logging**: Detailed logging to both console and log files

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- pandas>=1.5.0
- numpy>=1.21.0
- openpyxl>=3.0.0 (for .xlsx files)
- xlrd>=2.0.0 (for .xls files)

## Usage

### Basic Usage

Process files from the external directory:
```bash
python convert_excel_to_csv.py --external
```

Process files from the internal directory:
```bash
python convert_excel_to_csv.py --internal
```

Process files from both directories:
```bash
python convert_excel_to_csv.py --both
```

### Notes

- CSV files are created in the same directories as the original Excel files
- ZIP files are extracted to subdirectories named after the ZIP file
- The script preserves the original directory structure

## Output Structure

The script creates CSV files in the same directories as the original files:

```
data/
├── external/                    # Source directory
│   ├── file1.xlsx              # Original Excel file
│   ├── file1.csv               # Generated CSV file (same directory)
│   ├── subfolder/
│   │   ├── file2.xls           # Original Excel file
│   │   ├── file2.csv           # Generated CSV file (same directory)
│   │   ├── archive.zip         # Original ZIP file
│   │   └── archive/            # Extracted ZIP contents (subdirectory)
│   │       ├── sheet1.xlsx     # Excel file from ZIP
│   │       └── sheet1.csv      # Generated CSV file
│   └── ...
```

## File Naming Convention

- **Single sheet Excel files**: `original_filename.csv`
- **Multi-sheet Excel files**: `original_filename_sheetname.csv`
- **Files from ZIP archives**: Placed in a subdirectory named after the ZIP file

## Logging

The script creates detailed logs in the `logs/` directory:
- Log file: `logs/excel_to_csv_conversion.log`
- Console output: Real-time progress and summary information

## Performance

The script uses multiprocessing to leverage multiple CPU cores:
- Uses `CPU_COUNT - 1` worker processes by default
- Processes files in parallel for improved performance
- Shows processing time and statistics

## Error Handling

The script handles various error conditions gracefully:
- Corrupted Excel files
- Password-protected files
- Invalid ZIP archives
- Missing directories
- File permission issues

Failed files are logged with detailed error messages for troubleshooting.

## Examples

### Example 1: Convert all Excel files in external directory
```bash
cd /path/to/project/data/scripts/preprocessing
python convert_excel_to_csv.py --external
```

### Example 2: Process both directories
```bash
python convert_excel_to_csv.py --both
```

This will process files in both `data/external/` and `data/internal/` directories, creating CSV files alongside the original files.

## Supported File Types

- **.xlsx**: Excel 2007+ format (requires openpyxl)
- **.xls**: Excel 97-2003 format (requires xlrd)
- **.zip**: ZIP archives containing Excel files

## Notes

- CSV files are created in the same directories as the original Excel files
- Existing CSV files are overwritten if the script is run again
- ZIP files are extracted to subdirectories named after the ZIP file
- Invalid characters in sheet names are replaced with underscores
- The script skips files that are not Excel or ZIP files
