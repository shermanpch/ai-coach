# Data Sampler

This script creates sampled versions of CSV files for testing and development purposes.

## Features

- **Smart Sampling**: Files with >500 rows are sampled to 500 rows (or 500MB worth if 500 rows would exceed 500MB)
- **Automatic Copy**: Files with ≤500 rows are copied as-is
- **Parallel Processing**: Uses multiprocessing to speed up processing
- **Encoding Fallback**: Automatically tries latin-1 encoding if UTF-8 fails
- **Skip Existing**: Automatically skips files that already have sampled versions
- **Comprehensive Logging**: Detailed logging to track progress and identify issues
- **Performance Monitoring**: Tracks processing time and provides summary statistics

## Installation

Install the required dependencies:
```bash
pip install -r data/scripts/sampler/requirements.txt
```

## Usage

The script requires either the `--internal` or `--external` flag to specify the data source:

### For Internal Data
Process CSV files from `data/internal/` and save samples to `data/sample_internal/`:
```bash
python data/scripts/sampler/create_sample_data.py --internal
```

### For External Data
Process CSV files from `data/external/` and save samples to `data/sample_external/`:
```bash
python data/scripts/sampler/create_sample_data.py --external
```

### Help
To see all available options:
```bash
python data/scripts/sampler/create_sample_data.py --help
```

## How It Works

1. **File Discovery**: Finds all CSV files in the specified directory
2. **Size Analysis**: Analyzes file sizes and estimates which files need sampling
3. **Parallel Processing**: Processes multiple files simultaneously using all available CPU cores minus one
4. **Smart Sampling**: 
   - If file has ≤500 rows: copies as-is
   - If file has >500 rows: samples 500 rows (or fewer if 500 rows would exceed 500MB)
5. **Output**: Saves files with `sample_` prefix in the appropriate output directory

## Output Structure

```
data/
├── internal/                 # Original internal data
├── external/                 # Original external data  
├── sample_internal/          # Sampled internal data
│   ├── sample_file1.csv
│   ├── sample_file2.csv
│   └── ...
└── sample_external/          # Sampled external data
    ├── sample_file1.csv
    ├── sample_file2.csv
    └── ...
```

## Configuration

You can modify the following settings in the script:

- **target_rows**: Default sampling size (default: 500 rows)
- **target_size_gb**: Fallback size limit (default: 0.5 GB)
- **max_workers**: Number of parallel processes (default: CPU cores - 1)

## Performance Notes

- Large CSV files (>1GB) may take significant time and memory
- The script automatically uses all available CPU cores minus one
- Processing time varies based on file size and data complexity
- Memory usage scales with the largest CSV file being processed

## Troubleshooting

- If you encounter memory issues with very large files, consider reducing the number of workers
- Check the log file `sample_data_creation.log` for detailed error messages
- Ensure the source data directories exist:
  - `data/internal/` for `--internal` flag
  - `data/external/` for `--external` flag

## Examples

```bash
# Sample all internal data
python data/scripts/sampler/create_sample_data.py --internal

# Sample all external data
python data/scripts/sampler/create_sample_data.py --external
``` 