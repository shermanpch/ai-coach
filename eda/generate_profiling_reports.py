#!/usr/bin/env python3
"""
Script to generate ydata_profiling HTML reports for all CSV files in the data folder.
Uses multiprocessing for parallelization to speed up the process.
- Use --internal flag to generate reports from data/internal/ and save to eda/reports_internal/
- Use --external flag to generate reports from data/external/ and save to eda/reports_external/
- Preserves the original directory structure in the output folders
"""

import argparse
import logging
import multiprocessing as mp
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
from ydata_profiling import ProfileReport


def get_git_root():
    """Get the root directory of the git repository"""
    try:
        git_root_bytes = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        )
        git_root_str = git_root_bytes.strip().decode("utf-8")
        return Path(git_root_str)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


PROJECT_ROOT = get_git_root()
if PROJECT_ROOT is None:
    print(
        "CRITICAL: Error: Not in a git repository or git not found. Cannot determine project root.",
        file=sys.stderr,
    )
    sys.exit(1)

LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
EDA_DIR = PROJECT_ROOT / "eda"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging with absolute path
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "generate_profiling_reports.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def process_csv_file(args_tuple):
    """
    Process a single CSV file and generate its profiling report.

    Args:
        args_tuple: Tuple containing (csv_file_path, relative_path, output_base_dir)

    Returns:
        tuple: (relative_path, success_status, processing_time, error_message)
    """
    csv_file_path, relative_path, output_base_dir = args_tuple
    start_time = time.time()

    try:
        # Create output path maintaining directory structure
        output_dir = os.path.join(output_base_dir, os.path.dirname(relative_path))
        csv_filename = os.path.basename(relative_path)
        output_file = os.path.join(
            output_dir, f"{os.path.splitext(csv_filename)[0]}_profile_report.html"
        )

        # Check if report already exists
        if os.path.exists(output_file):
            processing_time = time.time() - start_time
            logger.info(f"Report already exists for {relative_path}, skipping...")
            return (
                relative_path,
                True,
                processing_time,
                "Skipped - report already exists",
            )

        logger.info(f"Starting processing: {relative_path}")

        # Read CSV file with encoding fallback
        logger.info(f"Reading CSV file: {relative_path}")
        df = None
        try:
            # Try default encoding first (usually UTF-8)
            df = pd.read_csv(csv_file_path)
        except UnicodeDecodeError:
            logger.warning(
                f"UTF-8 encoding failed for {relative_path}, trying latin-1 encoding..."
            )
            try:
                df = pd.read_csv(csv_file_path, encoding="latin-1")
                logger.info(
                    f"Successfully loaded {relative_path} with latin-1 encoding"
                )
            except Exception as e2:
                raise Exception(
                    f"Failed to read with both UTF-8 and latin-1 encodings: {str(e2)}"
                ) from e2

        logger.info(
            f"Loaded {relative_path}: {df.shape[0]} rows, {df.shape[1]} columns"
        )

        # Create profile report
        logger.info(f"Generating profile report for: {relative_path}")
        profile = ProfileReport(
            df,
            title=f"Data Profile Report - {relative_path}",
            explorative=True,
            minimal=False,  # Set to True for faster but less detailed reports
        )

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save the report
        logger.info(f"Saving report to: {output_file}")
        profile.to_file(output_file)

        processing_time = time.time() - start_time
        logger.info(
            f"Successfully processed {relative_path} in {processing_time:.2f} seconds"
        )

        return (relative_path, True, processing_time, None)

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error processing {relative_path}: {str(e)}"
        logger.error(error_msg)
        return (relative_path, False, processing_time, error_msg)


def get_csv_files(data_folder):
    """
    Get all CSV files from the data folder recursively, maintaining relative paths.

    Args:
        data_folder (str): Path to the data folder

    Returns:
        list: List of tuples (absolute_path, relative_path)
    """
    csv_files = []
    data_path = Path(data_folder)

    if not data_path.exists():
        logger.error(f"Data folder not found: {data_folder}")
        return csv_files

    # Recursively find all CSV files
    for file_path in data_path.rglob("*.csv"):
        # Calculate relative path from the data folder
        relative_path = file_path.relative_to(data_path)
        csv_files.append((str(file_path), str(relative_path)))

    logger.info(f"Found {len(csv_files)} CSV files in {data_folder}")
    return csv_files


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate ydata_profiling HTML reports for CSV files from internal or external data sources."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--internal",
        action="store_true",
        help="Generate reports from data/internal/ directory and save to eda/reports_internal/",
    )
    group.add_argument(
        "--external",
        action="store_true",
        help="Generate reports from data/external/ directory and save to eda/reports_external/",
    )

    return parser.parse_args()


def main():
    """
    Main function to orchestrate the profiling report generation.
    """
    # Parse command line arguments
    args = parse_arguments()

    # Determine source and output directories based on flags
    if args.internal:
        data_folder = "internal"
        output_folder = "reports_internal"
        data_type = "internal"
    elif args.external:
        data_folder = "external"
        output_folder = "reports_external"
        data_type = "external"

    # Use absolute paths
    data_folder_path = DATA_DIR / data_folder
    output_folder_path = EDA_DIR / output_folder

    max_workers = mp.cpu_count() - 1  # Leave one CPU core free

    logger.info(
        f"Starting profiling report generation for {data_type} data with {max_workers} workers"
    )
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Source directory: {data_folder_path}")
    logger.info(f"Output directory: {output_folder_path}")
    logger.info(f"Available CPU cores: {mp.cpu_count()}")

    # Get all CSV files
    csv_files = get_csv_files(str(data_folder_path))

    if not csv_files:
        logger.warning(f"No CSV files found in the {data_type} data folder")
        return

    # Process files in parallel
    start_time = time.time()

    logger.info(f"Processing {len(csv_files)} files using {max_workers} workers...")

    # Create argument tuples for multiprocessing
    process_args = [
        (csv_file, relative_path, str(output_folder_path))
        for csv_file, relative_path in csv_files
    ]

    with mp.Pool(processes=max_workers) as pool:
        results = pool.map(process_csv_file, process_args)

    # Summary
    total_time = time.time() - start_time
    successful = sum(1 for _, success, _, error in results if success and error is None)
    skipped = sum(
        1 for _, success, _, error in results if success and error is not None
    )
    failed = sum(1 for _, success, _, _ in results if not success)

    logger.info("=" * 60)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {len(csv_files)}")
    logger.info(f"Successfully generated: {successful}")
    logger.info(f"Skipped (already exists): {skipped}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    logger.info(f"Average time per file: {total_time / len(csv_files):.2f} seconds")

    # Detailed results
    logger.info("\nDETAILED RESULTS:")
    for relative_path, success, proc_time, error in results:
        if success and error is None:
            status = "SUCCESS"
        elif success and error is not None:
            status = "SKIPPED"
        else:
            status = "FAILED"
        logger.info(f"{relative_path}: {status} ({proc_time:.2f}s)")
        if error and not error.startswith("Skipped"):
            logger.error(f"  Error: {error}")

    if failed > 0:
        logger.warning(
            f"\n{failed} files failed to process. Check the log for details."
        )
    elif skipped > 0:
        logger.info(
            f"\n{skipped} files were skipped (reports already exist). {successful} new reports generated."
        )
    else:
        logger.info("\nAll files processed successfully!")


if __name__ == "__main__":
    main()
