#!/usr/bin/env python3
"""
Script to download Georgia education data from GOSA (Governor's Office of Student Achievement).
Downloads CSV files from https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data
and organizes them by data category in the external/ folder.

Features parallel downloading with anti-detection measures including:
- User agent rotation
- Random delays between requests
- Session management
- Respectful rate limiting

Usage:
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py [--categories CATEGORY1,CATEGORY2] [--years YEAR1,YEAR2] [--workers N] [--no-delays] [--dry-run]

Examples:
    # Download all data with anti-detection measures (recommended)
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py

    # Download only ACT scores and AP scores
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --categories "ACT Scores,Advanced Placement (AP) Scores"

    # Download only recent years (2020-2024)
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --years 2020-21,2021-22,2022-23,2023-24

    # Download with 2 parallel workers (safer for avoiding detection)
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --workers 2

    # Fast download without delays (higher risk of being blocked)
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --no-delays --workers 1

    # Dry run to see what would be downloaded
    python data/scripts/scraper/georgia_education_data/download_georgia_education_data.py --dry-run
"""

import argparse
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)

DATA_DIR = PROJECT_ROOT / "data"

# Base URL for the GOSA downloadable data page
BASE_URL = "https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data"
DOWNLOAD_BASE_URL = "https://download.gosa.ga.gov/"

# User agents to rotate through to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
]


# Create a session with anti-detection headers
def create_session():
    """Create a requests session with anti-detection measures."""
    session = requests.Session()

    # Set headers to mimic a real browser
    session.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    )

    return session


def sanitize_folder_name(name):
    """
    Sanitize folder name by removing special characters and converting to lowercase.

    Args:
        name (str): Original folder name

    Returns:
        str: Sanitized folder name
    """
    # Remove parentheses and special characters, replace spaces with underscores
    sanitized = re.sub(r"[^\w\s-]", "", name)
    sanitized = re.sub(r"[-\s]+", "_", sanitized)
    return sanitized.lower().strip("_")


def extract_year_from_link(link_text):
    """
    Extract year from link text (e.g., "2023-24" from link text).

    Args:
        link_text (str): Link text or filename

    Returns:
        str or None: Extracted year or None if not found
    """
    # Look for patterns like 2023-24, 2022-23, etc.
    year_pattern = r"20\d{2}-\d{2}"
    match = re.search(year_pattern, link_text)
    if match:
        return match.group()

    # Look for single years like 2023, 2022, etc.
    year_pattern = r"20\d{2}"
    match = re.search(year_pattern, link_text)
    if match:
        return match.group()

    return None


def parse_data_table(soup):
    """
    Parse the data table from the GOSA webpage to extract download links.

    Args:
        soup (BeautifulSoup): Parsed HTML content

    Returns:
        dict: Dictionary with category names as keys and list of download info as values
    """
    data_categories = {}

    # Find the main data table
    tables = soup.find_all("table")

    for table in tables:
        # Skip tables that contain "Retired Reporting" in their content
        table_text = table.get_text()
        if (
            "Retired Reporting" in table_text
            or "Retired Georgia Assessments" in table_text
        ):
            continue

        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 3:  # Should have category, description, and download links
                category_cell = cells[0]
                description_cell = cells[1]
                download_cell = cells[2]

                # Extract category name
                category_name = category_cell.get_text(strip=True)

                # Skip header rows, empty categories, and retired items
                if (
                    not category_name
                    or category_name.upper() in ["DATA CATEGORY", "RETIRED REPORTING"]
                    or "(Retired)" in category_name
                ):
                    continue

                # Extract download links
                links = download_cell.find_all("a", href=True)
                download_info = []

                for link in links:
                    href = link["href"]
                    link_text = link.get_text(strip=True)
                    year = extract_year_from_link(link_text)

                    # Process CSV, XLS, XLSX, and ZIP files
                    if href.endswith((".csv", ".xls", ".xlsx", ".zip")):
                        download_info.append(
                            {
                                "url": href,
                                "text": link_text,
                                "year": year,
                                "filename": os.path.basename(urlparse(href).path),
                            }
                        )

                if download_info:
                    data_categories[category_name] = {
                        "description": description_cell.get_text(strip=True),
                        "downloads": download_info,
                    }

    return data_categories


def download_file(url, local_path, max_retries=3, session=None):
    """
    Download a file from URL to local path with retry logic and anti-detection measures.

    Args:
        url (str): URL to download from
        local_path (str): Local path to save the file
        max_retries (int): Maximum number of retry attempts
        session (requests.Session): Optional session to use for the request

    Returns:
        tuple: (bool, str, str) - (success, url, local_path)
    """
    if session is None:
        session = create_session()

    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {url} to {local_path} (attempt {attempt + 1})")

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Add random delay to avoid being detected as a bot
            if attempt > 0:
                delay = random.uniform(1, 3) + (2**attempt)
                logger.info(f"Waiting {delay:.1f} seconds before retry...")
                time.sleep(delay)
            else:
                # Small random delay even on first attempt
                time.sleep(random.uniform(0.5, 2.0))

            # Rotate user agent for each attempt
            session.headers["User-Agent"] = random.choice(USER_AGENTS)

            # Add referer header to make request look more legitimate
            if "gosa.ga.gov" in url or "gosa.georgia.gov" in url:
                session.headers["Referer"] = BASE_URL

            # Download the file using requests session
            response = session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Write the file in chunks to handle large files
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify the file was downloaded and has content
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                file_size = os.path.getsize(local_path) / (1024 * 1024)  # Size in MB
                logger.info(
                    f"Successfully downloaded {os.path.basename(local_path)} ({file_size:.2f} MB)"
                )
                return True, url, local_path
            else:
                logger.warning(
                    f"Downloaded file is empty or doesn't exist: {local_path}"
                )

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(
                    f"Forbidden (403) error for {url}. Trying with different user agent..."
                )
                # Force a new user agent on 403 errors
                session.headers["User-Agent"] = random.choice(USER_AGENTS)
            elif e.response.status_code == 429:
                logger.warning(f"Rate limited (429) for {url}. Waiting longer...")
                time.sleep(random.uniform(5, 10))
            logger.error(f"HTTP error {e.response.status_code} for {url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")

        if attempt < max_retries - 1:
            # Exponential backoff with jitter
            delay = (2**attempt) + random.uniform(1, 3)
            logger.info(f"Waiting {delay:.1f} seconds before next attempt...")
            time.sleep(delay)

    logger.error(f"Failed to download {url} after {max_retries} attempts")
    return False, url, local_path


def download_files_parallel(
    download_tasks, max_workers=4, delay_between_downloads=True
):
    """
    Download multiple files in parallel using ThreadPoolExecutor with anti-detection measures.

    Args:
        download_tasks (list): List of tuples (url, local_path)
        max_workers (int): Maximum number of parallel workers
        delay_between_downloads (bool): Whether to add delays between downloads

    Returns:
        tuple: (successful_downloads, failed_downloads)
    """
    successful_downloads = 0
    failed_downloads = 0
    total_tasks = len(download_tasks)
    completed_tasks = 0

    # Limit workers to avoid overwhelming the server
    max_workers = min(max_workers, 3)  # Cap at 3 to be more respectful

    logger.info(f"Starting parallel downloads with {max_workers} workers")
    logger.info(f"Total files to download: {total_tasks}")
    logger.info(
        "Using anti-detection measures: user agent rotation, delays, and session management"
    )

    # Create a session for each worker to maintain consistency
    sessions = [create_session() for _ in range(max_workers)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit download tasks with staggered timing
        future_to_task = {}

        for i, (url, local_path) in enumerate(download_tasks):
            # Use round-robin to assign sessions to workers
            session = sessions[i % len(sessions)]

            # Add a small delay between task submissions to avoid burst requests
            if delay_between_downloads and i > 0:
                time.sleep(random.uniform(0.1, 0.5))

            future = executor.submit(download_file, url, local_path, 3, session)
            future_to_task[future] = (url, local_path)

        # Process completed downloads
        for future in as_completed(future_to_task):
            url, local_path = future_to_task[future]
            completed_tasks += 1

            try:
                success, _, _ = future.result()
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads += 1

                # Log progress every 5 files or at the end (more frequent for better feedback)
                if completed_tasks % 5 == 0 or completed_tasks == total_tasks:
                    logger.info(
                        f"Progress: {completed_tasks}/{total_tasks} files completed "
                        f"({successful_downloads} successful, {failed_downloads} failed)"
                    )

                # Add a small delay between processing completed downloads
                if delay_between_downloads and completed_tasks < total_tasks:
                    time.sleep(random.uniform(0.2, 0.8))

            except Exception as e:
                logger.error(f"Download task failed for {url}: {str(e)}")
                failed_downloads += 1

    return successful_downloads, failed_downloads


def filter_downloads(data_categories, selected_categories=None, selected_years=None):
    """
    Filter downloads based on selected categories and years.

    Args:
        data_categories (dict): All available data categories
        selected_categories (list): List of category names to include (None for all)
        selected_years (list): List of years to include (None for all)

    Returns:
        dict: Filtered data categories
    """
    filtered_categories = {}

    for category_name, category_data in data_categories.items():
        # Filter by category
        if selected_categories and category_name not in selected_categories:
            continue

        filtered_downloads = []
        for download in category_data["downloads"]:
            # Filter by year
            if (
                selected_years
                and download["year"]
                and download["year"] not in selected_years
            ):
                continue
            filtered_downloads.append(download)

        if filtered_downloads:
            filtered_categories[category_name] = {
                "description": category_data["description"],
                "downloads": filtered_downloads,
            }

    return filtered_categories


def main():
    parser = argparse.ArgumentParser(
        description="Download Georgia education data from GOSA website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--categories",
        type=str,
        help="Comma-separated list of data categories to download (default: all)",
    )

    parser.add_argument(
        "--years",
        type=str,
        help="Comma-separated list of years to download (e.g., '2023-24,2022-23')",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without actually downloading",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_DIR / "external"),
        help=f"Output directory for downloaded files (default: {DATA_DIR / 'external'})",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel download workers (default: 4, max: 3 for anti-detection)",
    )

    parser.add_argument(
        "--no-delays",
        action="store_true",
        help="Disable random delays between downloads (faster but more detectable)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts for failed downloads (default: 3)",
    )

    args = parser.parse_args()

    # Parse selected categories and years
    selected_categories = None
    if args.categories:
        selected_categories = [cat.strip() for cat in args.categories.split(",")]

    selected_years = None
    if args.years:
        selected_years = [year.strip() for year in args.years.split(",")]

    logger.info("Starting Georgia education data download")
    logger.info(f"Target URL: {BASE_URL}")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Output directory: {args.output_dir}")

    try:
        # Fetch the webpage with anti-detection measures
        logger.info("Fetching webpage content...")
        session = create_session()
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract data categories and download links
        logger.info("Parsing data table...")
        data_categories = parse_data_table(soup)

        if not data_categories:
            logger.error("No data categories found on the webpage")
            return

        logger.info(f"Found {len(data_categories)} data categories")

        # Filter based on user selection
        filtered_categories = filter_downloads(
            data_categories, selected_categories, selected_years
        )

        if not filtered_categories:
            logger.error("No data matches the specified filters")
            return

        logger.info(
            f"After filtering: {len(filtered_categories)} categories to process"
        )

        # Show what will be downloaded
        total_files = 0
        for category_name, category_data in filtered_categories.items():
            total_files += len(category_data["downloads"])
            logger.info(
                f"Category: {category_name} - {len(category_data['downloads'])} files"
            )

        logger.info(f"Total files to download: {total_files}")

        if args.dry_run:
            logger.info("DRY RUN - Showing what would be downloaded:")
            for category_name, category_data in filtered_categories.items():
                folder_name = sanitize_folder_name(category_name)
                logger.info(f"\nCategory: {category_name} -> {folder_name}/")
                for download in category_data["downloads"]:
                    year_folder = (
                        download["year"] if download["year"] else "unknown_year"
                    )
                    local_path = os.path.join(
                        args.output_dir, folder_name, year_folder, download["filename"]
                    )
                    logger.info(f"  {download['url']} -> {local_path}")
            return

        # Prepare download tasks
        download_tasks = []
        skipped_files = 0

        for category_name, category_data in filtered_categories.items():
            folder_name = sanitize_folder_name(category_name)
            logger.info(f"Preparing downloads for category: {category_name}")

            for download in category_data["downloads"]:
                year_folder = download["year"] if download["year"] else "unknown_year"
                local_path = os.path.join(
                    args.output_dir, folder_name, year_folder, download["filename"]
                )

                # Skip if file already exists
                if os.path.exists(local_path):
                    logger.info(f"File already exists, skipping: {local_path}")
                    skipped_files += 1
                    continue

                download_tasks.append((download["url"], local_path))

        logger.info(f"Prepared {len(download_tasks)} download tasks")
        logger.info(f"Skipped {skipped_files} existing files")

        if not download_tasks:
            logger.info("No files to download (all files already exist)")
            return

        # Download files in parallel with anti-detection measures
        successful_downloads, failed_downloads = download_files_parallel(
            download_tasks,
            max_workers=args.workers,
            delay_between_downloads=not args.no_delays,
        )

        # Summary
        logger.info("\nDownload Summary:")
        logger.info(f"Successful downloads: {successful_downloads}")
        logger.info(f"Failed downloads: {failed_downloads}")
        logger.info(f"Skipped files (already exist): {skipped_files}")
        logger.info(
            f"Total files processed: {successful_downloads + failed_downloads + skipped_files}"
        )

        if failed_downloads > 0:
            logger.warning("Some downloads failed. Check the log for details.")
        else:
            logger.info("All downloads completed successfully!")

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
