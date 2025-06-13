import argparse
import fcntl  # For file locking
import json
import os
import time
from functools import partial
from multiprocessing import Pool, cpu_count
from urllib.parse import quote_plus

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def create_driver():
    """Create a Chrome driver with optimized settings"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-images")  # Don't load images for faster loading
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    # Keep JavaScript enabled as Peterson's site likely needs it for search results
    return webdriver.Chrome(options=options)


def search_peterson_for_university(university_name):
    """Search Peterson's website for a university and extract all university links"""
    driver = create_driver()

    try:
        # URL encode the university name for the search
        encoded_name = quote_plus(university_name)
        search_url = f"https://www.petersons.com/search/college?q={encoded_name}"

        logger.info(f"Searching for: {university_name}")

        # Navigate to the search page
        driver.get(search_url)

        # Wait for search results to load dynamically
        wait = WebDriverWait(driver, 30)
        try:
            # Wait for the specific div that indicates search results are fully loaded
            wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[@class='mb-0 h5' and contains(text(), 'Showing 1 to 20 of the Top 1000 Undergrad Schools')]",
                    )
                )
            )
        except TimeoutException:
            logger.warning(f"Search results did not fully load for {university_name}")
            return {"search_query": university_name, "urls": []}

        # Single scroll to load any lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Brief wait for any additional content to load

        # Get the page source after scrolling
        html_content = driver.page_source

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all university links
        university_links = soup.find_all(
            "a", href=lambda x: x and "/college-search/" in x
        )

        # Extract URLs
        urls = []
        for link in university_links:
            href = link.get("href")
            if href and "/college-search/" in href:
                full_url = f"https://www.petersons.com{href}"
                if full_url not in urls:  # Avoid duplicates
                    urls.append(full_url)

        logger.info(f"Found {len(urls)} unique university URLs for {university_name}")
        return {"search_query": university_name, "urls": urls}

    except Exception as e:
        logger.error(f"Error searching for {university_name}: {str(e)}")
        return {"search_query": university_name, "urls": []}

    finally:
        driver.quit()


def load_existing_results():
    """Load existing results from the output file"""
    output_file = PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls.json"
    if output_file.exists():
        try:
            with open(output_file) as f:
                existing_results = json.load(f)
            logger.info(f"Loaded {len(existing_results)} existing results")
            return existing_results
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Could not load existing results, starting fresh")
            return []
    return []


def save_single_result(result):
    """Save a single result to the JSON file with file locking for thread safety"""
    output_file = PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls.json"
    backup_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls_backup.json"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    max_retries = 3
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            # Load existing results with file locking and backup recovery
            existing_results = []

            if output_file.exists():
                with open(output_file) as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                    try:
                        existing_results = json.load(f)
                        logger.debug(
                            f"Successfully loaded {len(existing_results)} existing results"
                        )
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON corruption detected in main file: {str(e)}")
                        # Try to recover from backup
                        if backup_file.exists():
                            try:
                                with open(backup_file) as backup_f:
                                    existing_results = json.load(backup_f)
                                logger.warning(
                                    f"Recovered {len(existing_results)} results from backup file"
                                )
                            except json.JSONDecodeError:
                                logger.error(
                                    "Backup file also corrupted! Starting fresh (this should not happen)"
                                )
                                existing_results = []
                        else:
                            logger.error(
                                "No backup file found! Starting fresh (data loss occurred)"
                            )
                            existing_results = []
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

            # Create dictionary for fast lookup and update
            results_dict = {r["search_query"]: r for r in existing_results}
            results_dict[result["search_query"]] = result
            updated_results = list(results_dict.values())

            # Write with exclusive file locking using atomic operation
            temp_file = output_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                try:
                    json.dump(updated_results, f, indent=2)
                    f.flush()  # Ensure data is written to disk
                    os.fsync(f.fileno())  # Force write to disk
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

            # Atomic move - this prevents corruption during write
            temp_file.replace(output_file)

            # Create synchronized backup AFTER successfully writing main file
            try:
                backup_temp_file = backup_file.with_suffix(".tmp")
                with open(backup_temp_file, "w") as backup_f:
                    fcntl.flock(backup_f.fileno(), fcntl.LOCK_EX)
                    try:
                        json.dump(
                            updated_results, backup_f, indent=2
                        )  # Use updated_results, not existing_results
                        backup_f.flush()
                        os.fsync(backup_f.fileno())
                    finally:
                        fcntl.flock(backup_f.fileno(), fcntl.LOCK_UN)

                # Atomic move for backup too
                backup_temp_file.replace(backup_file)
                logger.debug("Backup synchronized with main file")
            except Exception as backup_error:
                logger.warning(
                    f"Failed to create synchronized backup: {str(backup_error)}"
                )

            logger.info(
                f"Saved result for {result['search_query']} ({len(updated_results)} total results)"
            )
            return  # Success, exit the retry loop

        except OSError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"File lock conflict for {result['search_query']}, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"Failed to save result for {result['search_query']} after {max_retries} attempts: {str(e)}"
                )
        except Exception as e:
            logger.error(
                f"Unexpected error saving result for {result['search_query']}: {str(e)}"
            )
            break


def process_university_batch(universities_batch, existing_results_dict, delay=0.5):
    """Process a batch of universities with incremental saving"""
    batch_results = []

    for university_name in universities_batch:
        if university_name in existing_results_dict:
            logger.info(f"Skipping already processed university: {university_name}")
            result = existing_results_dict[university_name]
        else:
            logger.info(f"Processing new university: {university_name}")
            result = search_peterson_for_university(university_name)

            # Save result immediately after processing
            save_single_result(result)

            # Configurable delay to be respectful to the server
            time.sleep(delay)

        batch_results.append(result)

    return batch_results


def sync_backup_with_main():
    """Synchronize backup file with main file"""
    output_file = PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls.json"
    backup_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls_backup.json"
    )

    if not output_file.exists():
        logger.warning("Main file doesn't exist, cannot sync backup")
        return False

    try:
        # Read main file
        with open(output_file) as f:
            main_data = json.load(f)

        # Write to backup
        with open(backup_file, "w") as f:
            json.dump(main_data, f, indent=2)

        logger.info(
            f"Synchronized backup file with main file ({len(main_data)} entries)"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to sync backup with main: {str(e)}")
        return False


def compare_files():
    """Compare main and backup files and report differences"""
    output_file = PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls.json"
    backup_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls_backup.json"
    )

    main_data = []
    backup_data = []

    # Load main file
    if output_file.exists():
        try:
            with open(output_file) as f:
                main_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Main file corrupted: {str(e)}")
    else:
        logger.warning("Main file doesn't exist")

    # Load backup file
    if backup_file.exists():
        try:
            with open(backup_file) as f:
                backup_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Backup file corrupted: {str(e)}")
    else:
        logger.warning("Backup file doesn't exist")

    # Compare
    main_queries = {item["search_query"] for item in main_data}
    backup_queries = {item["search_query"] for item in backup_data}

    only_in_main = main_queries - backup_queries
    only_in_backup = backup_queries - main_queries

    logger.info("File comparison:")
    logger.info(f"  Main file: {len(main_data)} entries")
    logger.info(f"  Backup file: {len(backup_data)} entries")
    logger.info(f"  Only in main: {len(only_in_main)} entries")
    logger.info(f"  Only in backup: {len(only_in_backup)} entries")

    if only_in_main:
        logger.info(
            f"  Entries only in main: {list(only_in_main)[:5]}{'...' if len(only_in_main) > 5 else ''}"
        )
    if only_in_backup:
        logger.info(
            f"  Entries only in backup: {list(only_in_backup)[:5]}{'...' if len(only_in_backup) > 5 else ''}"
        )

    return {
        "main_count": len(main_data),
        "backup_count": len(backup_data),
        "only_in_main": only_in_main,
        "only_in_backup": only_in_backup,
        "in_sync": len(only_in_main) == 0 and len(only_in_backup) == 0,
    }


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape Peterson's website for university URLs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=cpu_count(),
        help="Number of worker processes to use for parallel processing",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of universities per batch (if not specified, calculated based on workers)",
    )

    parser.add_argument(
        "--num-batches",
        type=int,
        default=None,
        help="Total number of batches to create (if not specified, calculated based on workers)",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between requests to be respectful to the server",
    )

    parser.add_argument(
        "--sync-backup",
        action="store_true",
        help="Synchronize backup file with main file and exit",
    )

    parser.add_argument(
        "--compare-files",
        action="store_true",
        help="Compare main and backup files and exit",
    )

    return parser.parse_args()


def main():
    # Parse command line arguments
    args = parse_arguments()

    # Handle utility commands
    if args.compare_files:
        comparison = compare_files()
        if not comparison["in_sync"]:
            logger.warning("Files are not in sync!")
            if comparison["only_in_main"]:
                logger.info(
                    "Consider running --sync-backup to update backup with main file"
                )
        else:
            logger.info("Files are in sync!")
        return

    if args.sync_backup:
        if sync_backup_with_main():
            logger.info("Backup synchronization completed successfully")
        else:
            logger.error("Backup synchronization failed")
        return

    # Load the universities CSV
    csv_path = PROJECT_ROOT / "data" / "external" / "Comprehensive List of Uni.csv"
    logger.info(f"Looking for CSV file at: {csv_path}")
    logger.info(f"CSV file exists: {csv_path.exists()}")
    logger.info(f"Current working directory: {os.getcwd()}")

    if not csv_path.exists():
        logger.error(f"CSV file not found at {csv_path}")
        return

    universities = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(universities)} universities from CSV")

    # Get university names
    university_names = universities["University"].tolist()

    # Load existing results to avoid reprocessing
    existing_results = load_existing_results()
    existing_results_dict = {
        result["search_query"]: result for result in existing_results
    }

    # Filter out universities that have already been processed
    universities_to_process = [
        name for name in university_names if name not in existing_results_dict
    ]
    already_processed_count = len(university_names) - len(universities_to_process)

    logger.info(f"Total universities: {len(university_names)}")
    logger.info(f"Already processed: {already_processed_count}")
    logger.info(f"Remaining to process: {len(universities_to_process)}")

    if not universities_to_process:
        logger.info("All universities have already been processed!")
        return

    # Determine number of processes and batch configuration
    num_processes = min(
        args.workers, len(university_names)
    )  # Don't use more workers than universities

    # Calculate batch configuration based on arguments
    if args.batch_size:
        batch_size = args.batch_size
        num_batches = (
            len(university_names) + batch_size - 1
        ) // batch_size  # Ceiling division
    elif args.num_batches:
        num_batches = min(args.num_batches, len(university_names))
        batch_size = (
            len(university_names) + num_batches - 1
        ) // num_batches  # Ceiling division
    else:
        # Default: calculate based on number of workers
        batch_size = (
            len(university_names) + num_processes - 1
        ) // num_processes  # Ceiling division
        num_batches = (len(university_names) + batch_size - 1) // batch_size

    logger.info("Configuration:")
    logger.info(f"  Workers: {num_processes}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Number of batches: {num_batches}")
    logger.info(f"  Delay between requests: {args.delay}s")

    # Split universities into batches
    batches = [
        university_names[i : i + batch_size]
        for i in range(0, len(university_names), batch_size)
    ]

    logger.info(
        f"Split {len(university_names)} universities into {len(batches)} batches"
    )

    try:
        # Use multiprocessing to process batches in parallel
        with Pool(processes=num_processes) as pool:
            # Use partial to pass existing_results_dict and delay to each batch
            process_func = partial(
                process_university_batch,
                existing_results_dict=existing_results_dict,
                delay=args.delay,
            )

            # Process batches in parallel
            batch_results = pool.map(process_func, batches)

            # Flatten results for final summary
            all_results = []
            for batch_result in batch_results:
                all_results.extend(batch_result)

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error during multiprocessing: {str(e)}")

    # Print final summary
    final_results = load_existing_results()
    total_urls = sum(len(result["urls"]) for result in final_results)
    logger.info(f"Final summary: {len(final_results)} universities processed")
    logger.info(f"Total URLs found: {total_urls}")

    # Log completion
    logger.info("Peterson URL scraping completed successfully")


if __name__ == "__main__":
    main()
