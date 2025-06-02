#!/usr/bin/env python3
"""
Script to convert Excel files (.xls/.xlsx) to CSV format and extract ZIP files.
- Converts all .xls and .xlsx files to CSV format in the same directories as the original files
- If Excel file has multiple sheets, creates separate CSV files named {filename}_{sheetname}.csv
- Extracts ZIP files to subdirectories and processes any Excel files found within them
- Uses multiprocessing for improved performance
- Use --internal flag to process files from internal/ directory
- Use --external flag to process files from external/ directory
- Use --both flag to process files from both directories
"""

import argparse
import logging
import multiprocessing as mp
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

# Get the absolute path to the project root (3 levels up from this script)
# Script is at: data/scripts/preprocessing/convert_excel_to_csv.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging with absolute path
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "excel_to_csv_conversion.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def get_file_size_mb(file_path):
    """Get file size in MB."""
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024**2)
    return size_mb


def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def extract_zip_file(zip_path, extract_to):
    """
    Extract ZIP file to specified directory.

    Args:
        zip_path (str): Path to ZIP file
        extract_to (str): Directory to extract to

    Returns:
        List[str]: List of extracted file paths
    """
    extracted_files = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
            extracted_files = [
                os.path.join(extract_to, name) for name in zip_ref.namelist()
            ]
        logger.info(f"Extracted {len(extracted_files)} files from {zip_path}")
    except Exception as e:
        logger.error(f"Error extracting ZIP file {zip_path}: {str(e)}")

    return extracted_files


def convert_excel_to_csv(excel_path, relative_path):
    """
    Convert Excel file to CSV format(s) in the same directory as the original file.

    Args:
        excel_path (str): Path to Excel file
        relative_path (str): Relative path for logging purposes

    Returns:
        List[str]: List of created CSV file paths
    """
    csv_files = []

    try:
        # Get the base filename without extension and the directory
        excel_file_path = Path(excel_path)
        base_filename = excel_file_path.stem
        output_dir = excel_file_path.parent

        # Read all sheets from Excel file
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names

        logger.info(
            f"Found {len(sheet_names)} sheet(s) in {relative_path}: {sheet_names}"
        )

        for sheet_name in sheet_names:
            # Read the sheet
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            # Create CSV filename
            if len(sheet_names) == 1:
                # Single sheet - use original filename
                csv_filename = f"{base_filename}.csv"
            else:
                # Multiple sheets - include sheet name
                sanitized_sheet_name = sanitize_filename(sheet_name)
                csv_filename = f"{base_filename}_{sanitized_sheet_name}.csv"

            # Save CSV in the same directory as the original Excel file
            csv_path = output_dir / csv_filename

            # Save to CSV
            df.to_csv(csv_path, index=False)
            csv_files.append(str(csv_path))

            logger.info(
                f"Converted sheet '{sheet_name}' to {csv_path} ({len(df)} rows, {len(df.columns)} columns)"
            )

    except Exception as e:
        logger.error(f"Error converting Excel file {relative_path}: {str(e)}")

    return csv_files


def process_file(args_tuple):
    """
    Process a single file - convert Excel to CSV or extract ZIP and process contents.

    Args:
        args_tuple: Tuple containing (file_path, relative_path)

    Returns:
        tuple: (relative_path, success_status, processing_time, error_message, action_taken, files_created)
    """
    file_path, relative_path = args_tuple
    start_time = time.time()
    files_created = []

    try:
        file_size_mb = get_file_size_mb(file_path)
        file_ext = Path(file_path).suffix.lower()
        logger.info(
            f"Processing {relative_path} (Size: {file_size_mb:.2f} MB, Type: {file_ext})"
        )

        if file_ext in [".xls", ".xlsx"]:
            # Convert Excel file to CSV in the same directory
            csv_files = convert_excel_to_csv(file_path, relative_path)
            files_created.extend(csv_files)
            action_taken = f"CONVERTED_EXCEL ({len(csv_files)} CSV files)"

        elif file_ext == ".zip":
            # Extract ZIP file and process any Excel files within
            zip_dir = Path(file_path).parent
            zip_base_name = Path(file_path).stem
            extract_dir = zip_dir / zip_base_name

            # Create extraction directory in the same folder as the ZIP
            extract_dir.mkdir(exist_ok=True)

            extracted_files = extract_zip_file(file_path, str(extract_dir))

            excel_files_in_zip = []
            for extracted_file in extracted_files:
                if os.path.isfile(extracted_file):
                    ext = Path(extracted_file).suffix.lower()
                    if ext in [".xls", ".xlsx"]:
                        excel_files_in_zip.append(extracted_file)

            logger.info(
                f"Found {len(excel_files_in_zip)} Excel file(s) in ZIP: {relative_path}"
            )

            # Process each Excel file found in the ZIP
            for excel_file in excel_files_in_zip:
                # Create relative path for the Excel file within the ZIP
                excel_relative = os.path.relpath(excel_file, str(extract_dir))
                excel_in_zip_relative = os.path.join(zip_base_name, excel_relative)

                csv_files = convert_excel_to_csv(excel_file, excel_in_zip_relative)
                files_created.extend(csv_files)

            action_taken = f"EXTRACTED_ZIP ({len(excel_files_in_zip)} Excel files, {len(files_created)} CSV files)"

        else:
            # Unsupported file type
            action_taken = "SKIPPED_UNSUPPORTED"
            logger.info(f"Skipping unsupported file type: {relative_path}")

        processing_time = time.time() - start_time
        logger.info(
            f"Successfully processed {relative_path} in {processing_time:.2f} seconds"
        )

        return (relative_path, True, processing_time, None, action_taken, files_created)

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error processing {relative_path}: {str(e)}"
        logger.error(error_msg)
        return (
            relative_path,
            False,
            processing_time,
            error_msg,
            "FAILED",
            files_created,
        )


def get_target_files(data_folder):
    """
    Get all Excel and ZIP files from the data folder recursively.

    Args:
        data_folder (str): Path to the data folder

    Returns:
        list: List of tuples (absolute_path, relative_path)
    """
    target_files = []
    data_path = Path(data_folder)

    if not data_path.exists():
        logger.error(f"Data folder not found: {data_folder}")
        return target_files

    # Target file extensions
    target_extensions = [".xls", ".xlsx", ".zip"]

    # Recursively find all target files
    for ext in target_extensions:
        for file_path in data_path.rglob(f"*{ext}"):
            # Calculate relative path from the data folder
            relative_path = file_path.relative_to(data_path)
            target_files.append((str(file_path), str(relative_path)))

    logger.info(f"Found {len(target_files)} target files in {data_folder}")
    return target_files


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Convert Excel files to CSV and extract ZIP files containing Excel files. CSV files are created in the same directories as the original files."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--internal",
        action="store_true",
        help="Process files from internal/ directory",
    )
    group.add_argument(
        "--external",
        action="store_true",
        help="Process files from external/ directory",
    )
    group.add_argument(
        "--both",
        action="store_true",
        help="Process files from both internal/ and external/ directories",
    )

    return parser.parse_args()


def process_directory(data_folder, data_type, max_workers):
    """
    Process all files in a single directory.

    Args:
        data_folder (Path): Source data folder
        data_type (str): Type of data being processed
        max_workers (int): Number of worker processes

    Returns:
        dict: Processing statistics
    """
    logger.info(f"Processing {data_type} data...")
    logger.info(f"Source directory: {data_folder}")
    logger.info(
        "CSV files will be created in the same directories as the original files"
    )

    # Get all target files
    target_files = get_target_files(str(data_folder))

    if not target_files:
        logger.warning(f"No Excel or ZIP files found in the {data_type} data folder")
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "excel_converted": 0,
            "zip_extracted": 0,
            "csv_files_created": 0,
        }

    # Show file analysis
    logger.info(f"\nFILE ANALYSIS for {data_type}:")
    logger.info("=" * 50)
    excel_count = 0
    zip_count = 0
    total_size = 0

    for file_path, relative_path in target_files:
        size_mb = get_file_size_mb(file_path)
        total_size += size_mb
        ext = Path(file_path).suffix.lower()

        if ext in [".xls", ".xlsx"]:
            excel_count += 1
            logger.info(f"{relative_path}: {size_mb:.2f} MB (Excel)")
        elif ext == ".zip":
            zip_count += 1
            logger.info(f"{relative_path}: {size_mb:.2f} MB (ZIP)")

    logger.info(f"\nTotal files: {len(target_files)}")
    logger.info(f"Excel files: {excel_count}")
    logger.info(f"ZIP files: {zip_count}")
    logger.info(f"Total size: {total_size:.2f} MB")
    logger.info("=" * 50)

    # Process files in parallel
    start_time = time.time()

    logger.info(
        f"\nProcessing {len(target_files)} files using {max_workers} workers..."
    )

    # Create argument tuples for multiprocessing
    process_args = [
        (file_path, relative_path) for file_path, relative_path in target_files
    ]

    with mp.Pool(processes=max_workers) as pool:
        results = pool.map(process_file, process_args)

    # Calculate statistics
    total_time = time.time() - start_time
    successful = sum(1 for _, success, _, _, _, _ in results if success)
    failed = sum(1 for _, success, _, _, _, _ in results if not success)
    excel_converted = sum(
        1
        for _, success, _, _, action, _ in results
        if success and "CONVERTED_EXCEL" in action
    )
    zip_extracted = sum(
        1
        for _, success, _, _, action, _ in results
        if success and "EXTRACTED_ZIP" in action
    )
    csv_files_created = sum(
        len(files) for _, success, _, _, _, files in results if success
    )

    # Log summary for this directory
    logger.info(f"\n{data_type.upper()} PROCESSING SUMMARY:")
    logger.info("=" * 50)
    logger.info(f"Total files processed: {len(target_files)}")
    logger.info(f"Successfully processed: {successful}")
    logger.info(f"  - Excel files converted: {excel_converted}")
    logger.info(f"  - ZIP files extracted: {zip_extracted}")
    logger.info(f"Failed: {failed}")
    logger.info(f"CSV files created: {csv_files_created}")
    logger.info(f"Processing time: {total_time:.2f} seconds")

    return {
        "total": len(target_files),
        "successful": successful,
        "failed": failed,
        "excel_converted": excel_converted,
        "zip_extracted": zip_extracted,
        "csv_files_created": csv_files_created,
        "processing_time": total_time,
        "results": results,
    }


def main():
    """
    Main function to orchestrate the Excel to CSV conversion.
    """
    # Parse command line arguments
    args = parse_arguments()

    max_workers = mp.cpu_count() - 1  # Leave one CPU core free

    logger.info("Starting Excel to CSV conversion process")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Available CPU cores: {mp.cpu_count()}")
    logger.info(f"Using {max_workers} worker processes")
    logger.info(
        "CSV files will be created in the same directories as the original files"
    )

    # Determine which directories to process
    directories_to_process = []

    if args.internal or args.both:
        data_folder = DATA_DIR / "internal"
        directories_to_process.append((data_folder, "internal"))

    if args.external or args.both:
        data_folder = DATA_DIR / "external"
        directories_to_process.append((data_folder, "external"))

    # Process each directory
    all_stats = {}
    overall_start_time = time.time()

    for data_folder, data_type in directories_to_process:
        stats = process_directory(data_folder, data_type, max_workers)
        all_stats[data_type] = stats

    # Overall summary
    overall_time = time.time() - overall_start_time
    total_files = sum(stats["total"] for stats in all_stats.values())
    total_successful = sum(stats["successful"] for stats in all_stats.values())
    total_failed = sum(stats["failed"] for stats in all_stats.values())
    total_excel = sum(stats["excel_converted"] for stats in all_stats.values())
    total_zip = sum(stats["zip_extracted"] for stats in all_stats.values())
    total_csv = sum(stats["csv_files_created"] for stats in all_stats.values())

    logger.info("\n" + "=" * 60)
    logger.info("OVERALL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Directories processed: {len(directories_to_process)}")
    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Successfully processed: {total_successful}")
    logger.info(f"  - Excel files converted: {total_excel}")
    logger.info(f"  - ZIP files extracted: {total_zip}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Total CSV files created: {total_csv}")
    logger.info(f"Overall processing time: {overall_time:.2f} seconds")

    if total_files > 0:
        logger.info(f"Average time per file: {overall_time/total_files:.2f} seconds")

    # Detailed results for each directory
    for data_type, stats in all_stats.items():
        if "results" in stats:
            logger.info(f"\nDETAILED RESULTS for {data_type.upper()}:")
            for relative_path, success, proc_time, error, action, files in stats[
                "results"
            ]:
                status = "SUCCESS" if success else "FAILED"
                logger.info(f"{relative_path}: {status} ({action}) ({proc_time:.2f}s)")
                if not success and error:
                    logger.error(f"  Error: {error}")
                elif success and files:
                    logger.info(f"  Created: {len(files)} CSV file(s)")

    if total_failed > 0:
        logger.warning(
            f"\n{total_failed} files failed to process. Check the log for details."
        )
    else:
        logger.info("\nAll files processed successfully!")


if __name__ == "__main__":
    main()
