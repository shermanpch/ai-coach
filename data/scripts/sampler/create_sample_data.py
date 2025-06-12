#!/usr/bin/env python3
"""
Script to create sampled versions of CSV files.
- Files with >500 rows are sampled to 500 rows (or 500MB worth if 500 rows would exceed 500MB)
- Files with ≤500 rows are copied as-is
- All files are saved with 'sample_' prefix in the same directory structure
- Use --internal flag to sample from internal/ and save to sample_internal/
- Use --external flag to sample from external/ and save to sample_external/
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

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging with absolute path
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "create_sample_data.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def get_file_size_gb(file_path):
    """Get file size in GB."""
    size_bytes = os.path.getsize(file_path)
    size_gb = size_bytes / (1024**3)
    return size_gb


def estimate_sample_size(df, file_size_gb, target_rows=500, target_size_gb=0.5):
    """
    Estimate the sample size needed.
    Priority: 500 rows, but if that would exceed 500MB, use 500MB worth of rows.

    Args:
        df: DataFrame to sample
        file_size_gb: Original file size in GB
        target_rows: Target number of rows (default: 500)
        target_size_gb: Fallback target size in GB (default: 0.5)

    Returns:
        int: Number of rows to sample
    """
    total_rows = len(df)

    # If file has 500 or fewer rows, return all rows
    if total_rows <= target_rows:
        return total_rows

    # Calculate estimated size per row
    size_per_row_gb = file_size_gb / total_rows
    # Calculate estimated size for 500 rows
    estimated_size_500_rows = size_per_row_gb * target_rows

    # If 500 rows would be <= 500MB, use 500 rows
    if estimated_size_500_rows <= target_size_gb:
        return target_rows

    # Otherwise, calculate how many rows fit in 500MB
    rows_for_500mb = int(target_size_gb / size_per_row_gb)

    # Ensure the sample size does not exceed available rows
    return min(rows_for_500mb, total_rows)


def process_csv_file(args_tuple):
    """
    Process a single CSV file - sample to 500 rows or copy as-is.

    Args:
        args_tuple: Tuple containing (csv_file_path, relative_path, output_base_dir)

    Returns:
        tuple: (relative_path, success_status, processing_time, error_message, action_taken)
    """
    csv_file_path, relative_path, output_base_dir = args_tuple
    start_time = time.time()

    try:
        # Check file size
        file_size_gb = get_file_size_gb(csv_file_path)
        logger.info(f"Processing {relative_path} (Size: {file_size_gb:.2f} GB)")

        # Create output path maintaining directory structure
        output_dir = os.path.join(output_base_dir, os.path.dirname(relative_path))
        csv_filename = os.path.basename(relative_path)
        output_file = os.path.join(output_dir, f"sample_{csv_filename}")

        # Check if output file already exists
        if os.path.exists(output_file):
            processing_time = time.time() - start_time
            logger.info(f"Sample file already exists for {relative_path}, skipping...")
            return (
                relative_path,
                True,
                processing_time,
                "Skipped - sample already exists",
                "SKIPPED",
            )

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

        original_rows = len(df)
        logger.info(
            f"Loaded {relative_path}: {original_rows} rows, {df.shape[1]} columns"
        )

        # Determine sampling size
        sample_size = estimate_sample_size(df, file_size_gb)

        if sample_size < original_rows:
            # Sampling needed
            logger.info(f"Sampling {sample_size} rows from {original_rows} rows")

            # Determine reason for sampling
            if sample_size == 500:
                reason = "target 500 rows"
            else:
                reason = f"500MB limit (~{sample_size} rows)"

            logger.info(f"Sampling reason: {reason}")

            # Random sample
            df_sampled = df.sample(n=sample_size, random_state=42)
            action_taken = f"SAMPLED ({sample_size} rows)"
        else:
            # No sampling needed (file has ≤500 rows)
            df_sampled = df
            logger.info(f"File has {original_rows} rows (≤500), copying as-is")
            action_taken = "COPIED"

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save the file
        logger.info(f"Saving to: {output_file}")
        df_sampled.to_csv(output_file, index=False)

        # Verify output file size
        output_size_gb = get_file_size_gb(output_file)
        logger.info(f"Output file size: {output_size_gb:.2f} GB")

        processing_time = time.time() - start_time
        logger.info(
            f"Successfully processed {relative_path} in {processing_time:.2f} seconds"
        )

        return (relative_path, True, processing_time, None, action_taken)

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error processing {relative_path}: {str(e)}"
        logger.error(error_msg)
        return (relative_path, False, processing_time, error_msg, "FAILED")


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
        description="Create sampled versions of CSV files from internal or external data sources."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--internal",
        action="store_true",
        help="Sample data from internal/ directory and save to sample_internal/",
    )
    group.add_argument(
        "--external",
        action="store_true",
        help="Sample data from external/ directory and save to sample_external/",
    )

    return parser.parse_args()


def main():
    """
    Main function to orchestrate the sample data creation.
    """
    # Parse command line arguments
    args = parse_arguments()

    # Determine source and output directories based on flags
    if args.internal:
        data_folder = "internal"
        output_folder = "sample_internal"
        data_type = "internal"
    elif args.external:
        data_folder = "external"
        output_folder = "sample_external"
        data_type = "external"

    # Use absolute paths
    data_folder_path = DATA_DIR / data_folder
    output_folder_path = DATA_DIR / output_folder

    max_workers = mp.cpu_count() - 1  # Leave one CPU core free

    logger.info(
        f"Starting sample data creation for {data_type} data with {max_workers} workers"
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

    # Show file sizes before processing
    logger.info("\nFILE SIZE ANALYSIS:")
    logger.info("=" * 60)
    total_size = 0
    files_to_sample = 0

    # First pass: analyze which files need sampling
    for csv_file, relative_path in csv_files:
        size_gb = get_file_size_gb(csv_file)
        total_size += size_gb

        # Quick row count estimation (rough estimate based on file size)
        # A more accurate check will be performed during processing
        estimated_rows = size_gb * 1000000  # Very rough estimate: ~1M rows per GB

        if estimated_rows > 500:
            files_to_sample += 1
            logger.info(f"{relative_path}: {size_gb:.2f} GB (LIKELY TO BE SAMPLED)")
        else:
            logger.info(f"{relative_path}: {size_gb:.2f} GB (LIKELY COPIED AS-IS)")

    logger.info(f"\nTotal original size: {total_size:.2f} GB")
    logger.info(f"Files likely to be sampled: {files_to_sample}")
    logger.info(
        "Note: Final sampling decision based on actual row count during processing"
    )
    logger.info("=" * 60)

    # Process files in parallel
    start_time = time.time()

    logger.info(f"\nProcessing {len(csv_files)} files using {max_workers} workers...")

    # Create argument tuples for multiprocessing
    process_args = [
        (csv_file, relative_path, str(output_folder_path))
        for csv_file, relative_path in csv_files
    ]

    with mp.Pool(processes=max_workers) as pool:
        results = pool.map(process_csv_file, process_args)

    # Summary
    total_time = time.time() - start_time
    successful = sum(
        1 for _, success, _, error, _ in results if success and error is None
    )
    skipped = sum(
        1 for _, success, _, error, _ in results if success and error is not None
    )
    failed = sum(1 for _, success, _, _, _ in results if not success)
    sampled = sum(
        1 for _, success, _, _, action in results if success and "SAMPLED" in action
    )
    copied = sum(
        1 for _, success, _, _, action in results if success and action == "COPIED"
    )

    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {len(csv_files)}")
    logger.info(f"Successfully processed: {successful}")
    logger.info(f"  - Sampled (to 500 rows or 500MB): {sampled}")
    logger.info(f"  - Copied as-is (≤500 rows): {copied}")
    logger.info(f"Skipped (already exists): {skipped}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    logger.info(f"Average time per file: {total_time / len(csv_files):.2f} seconds")

    # Calculate estimated final size
    if output_folder_path.exists():
        final_size = sum(
            get_file_size_gb(str(f)) for f in output_folder_path.rglob("sample_*.csv")
        )
        logger.info(f"Final {output_folder} folder size: {final_size:.2f} GB")
        if total_size > 0:
            logger.info(
                f"Size reduction: {((total_size - final_size) / total_size * 100):.1f}%"
            )

    # Detailed results
    logger.info("\nDETAILED RESULTS:")
    for relative_path, success, proc_time, error, action in results:
        if success and error is None:
            status = f"SUCCESS ({action})"
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
            f"\n{skipped} files were skipped (samples already exist). {successful} new samples created."
        )
    else:
        logger.info("\nAll files processed successfully!")


if __name__ == "__main__":
    main()
