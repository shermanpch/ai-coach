import argparse
import fcntl
import json
import os
import time
from multiprocessing import Pool, cpu_count

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def load_peterson_urls(file_path):
    """Load the Peterson university URLs JSON file"""
    try:
        with open(file_path) as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} university search results")
        return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading file: {e}")
        return []


def json_to_dataframe(data):
    """Convert Peterson JSON data to DataFrame"""
    rows = []
    for entry in data:
        university = entry["search_query"]
        for url in entry["urls"]:
            rows.append({"University": university, "URL": url})
    return pd.DataFrame(rows)


def scrape_peterson_page(url, max_retries=3, delay=1):
    """Scrape a Peterson university page to extract name and location"""
    # Skip non-university pages
    skip_urls = [
        "international-students-guide.aspx",
        "graduate-schools-guide.aspx",
        "online-colleges-guide.aspx",
        "scholarship-search.aspx",
        "test-prep.aspx",
    ]

    if any(skip_url in url for skip_url in skip_urls):
        return {
            "name": None,
            "location": None,
            "success": False,
            "error": "Skipped non-university page",
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract university name from h1 tag
            name_element = soup.find("h1", class_="mb-1 pr-3 pl-0 h3 text-white")
            university_name = (
                name_element.get_text(strip=True) if name_element else None
            )

            # Extract location from p tag
            location_element = soup.find("p", class_="mb-0 h5 text-white")
            location = (
                location_element.get_text(strip=True) if location_element else None
            )

            time.sleep(delay)  # Be respectful to the server

            return {
                "name": university_name,
                "location": location,
                "success": True,
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                return {
                    "name": None,
                    "location": None,
                    "success": False,
                    "error": str(e),
                }
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return {
                "name": None,
                "location": None,
                "success": False,
                "error": str(e),
            }


def normalize_text(text):
    """Normalize text for comparison"""
    if not text:
        return ""
    import re

    return re.sub(r"\s+", " ", text.strip().lower())


def load_existing_matches():
    """Load existing matched universities from the validation results JSON"""
    output_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_url_validation_results.json"
    )
    backup_file = (
        PROJECT_ROOT
        / "data"
        / "cleaned"
        / "peterson_url_validation_results_backup.json"
    )

    existing_matches = []

    if output_file.exists():
        try:
            with open(output_file) as f:
                existing_matches = json.load(f)
            logger.info(f"Loaded {len(existing_matches)} existing validation results")
        except json.JSONDecodeError as e:
            logger.error(f"Main validation file corrupted: {str(e)}")
            # Try to recover from backup
            if backup_file.exists():
                try:
                    with open(backup_file) as backup_f:
                        existing_matches = json.load(backup_f)
                    logger.warning(
                        f"Recovered {len(existing_matches)} validation results from backup file"
                    )
                except json.JSONDecodeError:
                    logger.error(
                        "Backup validation file also corrupted! Starting fresh"
                    )
                    existing_matches = []
            else:
                logger.error("No backup validation file found! Starting fresh")
                existing_matches = []

    # Extract university names that already have been processed (any successful scrape)
    matched_universities = set()
    for result in existing_matches:
        # Consider ANY result as already processed (matches OR no-match entries)
        if result.get("Scrape_Success", False):
            matched_universities.add(result["University"])

    logger.info(
        f"Found {len(matched_universities)} universities that already have been processed"
    )
    return matched_universities


def save_matched_result(result):
    """Save only matched results to JSON with fcntl locking and backup recovery"""
    output_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_url_validation_results.json"
    )
    backup_file = (
        PROJECT_ROOT
        / "data"
        / "cleaned"
        / "peterson_url_validation_results_backup.json"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    max_retries = 5
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
                            f"Successfully loaded {len(existing_results)} existing validation results"
                        )
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"JSON corruption detected in main validation file: {str(e)}"
                        )
                        # Try to recover from backup
                        if backup_file.exists():
                            try:
                                with open(backup_file) as backup_f:
                                    existing_results = json.load(backup_f)
                                logger.warning(
                                    f"Recovered {len(existing_results)} validation results from backup file"
                                )
                            except json.JSONDecodeError:
                                logger.error(
                                    "Backup validation file also corrupted! Starting fresh"
                                )
                                existing_results = []
                        else:
                            logger.error(
                                "No backup validation file found! Starting fresh"
                            )
                            existing_results = []
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

            # Create dictionary for fast lookup and update using University as key
            # This allows multiple universities to share the same Peterson URL
            results_dict = {r["University"]: r for r in existing_results}
            results_dict[result["University"]] = result
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
                        json.dump(updated_results, backup_f, indent=2)
                        backup_f.flush()
                        os.fsync(backup_f.fileno())
                    finally:
                        fcntl.flock(backup_f.fileno(), fcntl.LOCK_UN)

                # Atomic move for backup too
                backup_temp_file.replace(backup_file)
                logger.debug("Backup synchronized with main validation file")
            except Exception as backup_error:
                logger.warning(
                    f"Failed to create synchronized backup: {str(backup_error)}"
                )

            logger.info(
                f"Saved validation result for University: {result['University']} -> {result['URL']} ({len(updated_results)} total universities processed)"
            )
            return  # Success, exit the retry loop

        except OSError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"File lock conflict for {result['URL']}, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"Failed to save validation result for {result['URL']} after {max_retries} attempts: {str(e)}"
                )
        except Exception as e:
            logger.error(
                f"Unexpected error saving validation result for {result['URL']}: {str(e)}"
            )
            break


def sync_backup_with_main():
    """Synchronize backup file with main file"""
    output_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_url_validation_results.json"
    )
    backup_file = (
        PROJECT_ROOT
        / "data"
        / "cleaned"
        / "peterson_url_validation_results_backup.json"
    )

    if not output_file.exists():
        logger.warning("Main validation file doesn't exist, cannot sync backup")
        return False

    try:
        # Read main file
        with open(output_file) as f:
            main_data = json.load(f)

        # Write to backup
        with open(backup_file, "w") as f:
            json.dump(main_data, f, indent=2)

        logger.info(
            f"Synchronized backup file with main validation file ({len(main_data)} entries)"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to sync backup with main: {str(e)}")
        return False


def compare_files():
    """Compare main and backup files and report differences"""
    output_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_url_validation_results.json"
    )
    backup_file = (
        PROJECT_ROOT
        / "data"
        / "cleaned"
        / "peterson_url_validation_results_backup.json"
    )

    main_data = []
    backup_data = []

    # Load main file
    if output_file.exists():
        try:
            with open(output_file) as f:
                main_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Main validation file corrupted: {str(e)}")
    else:
        logger.warning("Main validation file doesn't exist")

    # Load backup file
    if backup_file.exists():
        try:
            with open(backup_file) as f:
                backup_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Backup validation file corrupted: {str(e)}")
    else:
        logger.warning("Backup validation file doesn't exist")

    # Compare
    main_urls = {item["URL"] for item in main_data}
    backup_urls = {item["URL"] for item in backup_data}

    only_in_main = main_urls - backup_urls
    only_in_backup = backup_urls - main_urls

    logger.info("Validation file comparison:")
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


def process_university_urls(args):
    """Process all URLs for a single university"""
    university_name, university_urls, delay, matched_universities = args

    # Check if this university has already been processed
    if university_name in matched_universities:
        logger.info(f"Skipping {university_name} - already processed")
        return 0

    logger.info(f"Processing {university_name} ({len(university_urls)} URLs)")

    # Store all scraped results to find best match
    scraped_results = []

    for _, row in university_urls.iterrows():
        url = row["URL"]
        town = row["Town"]

        # Scrape the Peterson page
        scraped_data = scrape_peterson_page(url, delay=delay)

        if not scraped_data["success"]:
            continue

        # Check for matches
        expected_university = normalize_text(university_name)
        expected_location = normalize_text(town)
        scraped_university = normalize_text(scraped_data["name"])
        scraped_location = normalize_text(scraped_data["location"])

        # Determine if this is a name match
        name_match = (
            (
                expected_university in scraped_university
                or scraped_university in expected_university
            )
            if scraped_data["name"]
            else False
        )

        location_match = (
            (
                expected_location in scraped_location
                or scraped_location in expected_location
            )
            if scraped_data["location"]
            else False
        )

        overall_match = name_match and location_match

        # Store result with match information
        result_data = {
            "University": university_name,
            "URL": url,
            "Town": town,
            "Scraped_Name": scraped_data["name"],
            "Scraped_Location": scraped_data["location"],
            "Scrape_Success": True,
            "Name_Match": name_match,
            "Location_Match": location_match,
            "Overall_Match": overall_match,
            "Name_Similarity": None,  # Will be calculated only if needed for fuzzy matching
            "Error": "",
        }

        scraped_results.append(result_data)

        # Find best match: Two-pass approach
    best_match = None

    # PASS 1: Look for exact matches first
    # First, look for overall matches
    overall_matches = [r for r in scraped_results if r["Overall_Match"]]
    if overall_matches:
        best_match = overall_matches[0]
        logger.info(
            f"OVERALL MATCH FOUND: {university_name} -> {best_match['Scraped_Name']} in {best_match['Scraped_Location']}"
        )
    else:
        # If no overall matches, look for name matches
        name_matches = [r for r in scraped_results if r["Name_Match"]]
        if name_matches:
            best_match = name_matches[0]
            logger.info(
                f"NAME MATCH FOUND: {university_name} -> {best_match['Scraped_Name']} in {best_match['Scraped_Location']}"
            )
        else:
            # PASS 2: No matches found, try fuzzy matching
            logger.info(
                f"No matches found for {university_name}, trying fuzzy matching..."
            )

            # Find the result with highest similarity score (no threshold)
            if scraped_results:
                # Calculate similarity scores only now when needed for fuzzy matching
                expected_university = normalize_text(university_name)
                for result in scraped_results:
                    if result["Scraped_Name"]:
                        scraped_university = normalize_text(result["Scraped_Name"])
                        result["Name_Similarity"] = fuzz.ratio(
                            expected_university, scraped_university
                        )
                    else:
                        result["Name_Similarity"] = 0

                # Sort by similarity score (highest first)
                scraped_results.sort(key=lambda x: x["Name_Similarity"], reverse=True)
                best_match = scraped_results[0]

                # Keep the original match flags - fuzzy match is NOT a true name match
                # best_match["Name_Match"] remains False
                # best_match["Overall_Match"] remains False

                logger.info(
                    f"FUZZY MATCH FOUND (NOT NAME MATCH): {university_name} -> {best_match['Scraped_Name']} in {best_match['Scraped_Location']} "
                    f"(Name similarity: {best_match['Name_Similarity']}%)"
                )

    # Save the best match if found
    if best_match:
        save_matched_result(best_match)
        return 1  # Found a match
    else:
        # ALWAYS save an entry to mark this university as processed, even if all scrapes failed
        if scraped_results:
            # Use the first scraped result as a template, but mark as no match
            no_match_result = {
                "University": university_name,
                "URL": scraped_results[0]["URL"],  # Use first URL as representative
                "Town": scraped_results[0]["Town"],
                "Scraped_Name": scraped_results[0]["Scraped_Name"],
                "Scraped_Location": scraped_results[0]["Scraped_Location"],
                "Scrape_Success": True,
                "Name_Match": False,
                "Location_Match": False,
                "Overall_Match": False,
                "Name_Similarity": None,
                "Error": "No matches found after processing all URLs",
            }
            save_matched_result(no_match_result)
            logger.info(f"NO MATCH: {university_name} - marked as processed")
        else:
            # All URLs failed to scrape - still mark as processed to avoid retrying
            first_url = university_urls.iloc[0]  # Get first URL from the dataframe
            failed_scrape_result = {
                "University": university_name,
                "URL": first_url["URL"],
                "Town": first_url["Town"],
                "Scraped_Name": None,
                "Scraped_Location": None,
                "Scrape_Success": False,
                "Name_Match": False,
                "Location_Match": False,
                "Overall_Match": False,
                "Name_Similarity": None,
                "Error": "All URLs failed to scrape - marked as processed to avoid retrying",
            }
            save_matched_result(failed_scrape_result)
            logger.info(
                f"ALL SCRAPES FAILED: {university_name} - marked as processed to avoid retrying"
            )

    return 0  # No matches found


def validate_peterson_urls_multiprocessing(
    dataframe,
    delay_between_requests=2.0,
    num_processes=None,
):
    """Process universities using multiprocessing, only saving matches"""

    # Load existing matches to avoid reprocessing
    matched_universities = load_existing_matches()

    # Group URLs by university
    urls_by_university = dataframe.groupby("University")

    # Count total universities
    total_universities = len(list(urls_by_university))

    logger.info(f"Total university groups in dataset: {total_universities}")
    logger.info(f"Universities already processed: {len(matched_universities)}")

    # Prepare arguments for multiprocessing
    process_args = [
        (
            university_name,
            university_urls,
            delay_between_requests,
            matched_universities,
        )
        for university_name, university_urls in urls_by_university
    ]

    logger.info(
        f"Processing {len(process_args)} universities with {num_processes or cpu_count()} workers"
    )

    # Use multiprocessing
    if num_processes is None:
        num_processes = min(cpu_count(), len(process_args))

    matches_found = 0
    try:
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_university_urls, process_args)
            matches_found = sum(results)
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error during multiprocessing: {str(e)}")

    logger.info(f"Total matches found: {matches_found}")
    return matches_found


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Validate Peterson URLs and save only matched universities",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between requests",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=cpu_count(),
        help="Number of worker processes",
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
    args = parse_arguments()

    # Handle utility commands
    if args.compare_files:
        comparison = compare_files()
        if not comparison["in_sync"]:
            logger.warning("Validation files are not in sync!")
            if comparison["only_in_main"]:
                logger.info(
                    "Consider running --sync-backup to update backup with main file"
                )
        else:
            logger.info("Validation files are in sync!")
        return

    if args.sync_backup:
        if sync_backup_with_main():
            logger.info("Backup synchronization completed successfully")
        else:
            logger.error("Backup synchronization failed")
        return

    logger.info("Starting Peterson URL validation...")

    # Load universities CSV
    csv_path = PROJECT_ROOT / "data" / "external" / "Comprehensive List of Uni.csv"
    if not csv_path.exists():
        logger.error(f"CSV file not found at {csv_path}")
        return

    universities = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(universities)} universities from CSV")

    # Load Peterson URLs
    peterson_data = load_peterson_urls(
        PROJECT_ROOT / "data" / "cleaned" / "peterson_university_urls.json"
    )
    if not peterson_data:
        logger.error("No Peterson URL data found")
        return

    # Convert to DataFrame and merge
    peterson_df = json_to_dataframe(peterson_data)
    peterson_df = peterson_df[~peterson_df["URL"].isna()]

    to_filter = pd.merge(
        peterson_df,
        universities,
        on=["University"],
        how="left",
        validate="m:m",
    )

    # Count university-location combinations
    total_university_locations = len(to_filter.groupby(["University", "Town"]))

    logger.info(
        f"Processing {len(to_filter)} URLs for {total_university_locations} university-location combinations"
    )

    # Run validation
    matches_found = validate_peterson_urls_multiprocessing(
        to_filter, delay_between_requests=args.delay, num_processes=args.workers
    )

    print(f"\nValidation completed! Total matches found: {matches_found}")
    logger.info("Peterson URL validation completed successfully")


if __name__ == "__main__":
    main()
