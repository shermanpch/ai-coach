#!/usr/bin/env python3
"""
Script to scrape Majors & Degrees section from Peterson's web pages using BeautifulSoup
and output them in JSON format similar to the existing data structure.
"""

import argparse
import json
import logging
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

load_dotenv()

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Thread-safe logging lock
log_lock = threading.Lock()

# Change to project root
os.chdir(PROJECT_ROOT)


def thread_safe_log(level, message):
    """Thread-safe logging function"""
    with log_lock:
        logger.log(level, message)


def extract_university_name(soup):
    """Extract university name from the HTML"""
    # Try to find the university name in the h1 tag
    h1_tag = soup.find("h1", class_="mb-1 pr-3 pl-0 h3 text-white")
    if h1_tag:
        return h1_tag.get_text(strip=True)

    # Fallback to title tag
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        # Remove " - Tuition and Acceptance Rate" suffix if present
        return re.sub(r"\s*-\s*Tuition and Acceptance Rate.*$", "", title_text)

    return "Unknown University"


def extract_majors_and_degrees(soup):
    """Extract majors and degrees from the HTML structure"""
    majors_section = soup.find("section", id="degrees")
    if not majors_section:
        return []

    table = majors_section.find("table")
    if not table:
        return []

    categories = []
    current_category = None

    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = tbody.find_all("tr")

    for row in rows:
        th = row.find("th")
        if not th:
            continue

        # Check if this is a top-level category
        if "top-level" in th.get("class", []):
            category_name = th.get_text(strip=True)
            current_category = {"category": category_name, "programs": []}
            categories.append(current_category)
        else:
            # This is a program under the current category
            if current_category is None:
                continue

            program_name = th.get_text(strip=True)
            tds = row.find_all("td")

            # Check for Associate degree (first td after th)
            offers_associate = False
            offers_bachelors = False

            if len(tds) >= 2:
                # Check Associate column (first td)
                associate_td = tds[0]
                if associate_td.find("img", alt="Checkmark"):
                    offers_associate = True

                # Check Bachelors column (second td)
                bachelors_td = tds[1]
                if bachelors_td.find("img", alt="Checkmark"):
                    offers_bachelors = True

            program = {
                "name": program_name,
                "offers_associate": offers_associate,
                "offers_bachelors": offers_bachelors,
            }

            current_category["programs"].append(program)

    return categories


def scrape_university_courses(url: str, university_name: str = None) -> Dict[str, Any]:
    """Scrape a single university URL using requests and BeautifulSoup"""
    try:
        thread_safe_log(logging.INFO, f"Scraping: {url}")

        # Set up headers to mimic a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Make the request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract university name
        extracted_university_name = extract_university_name(soup)

        # Extract majors and degrees
        majors_and_degrees = extract_majors_and_degrees(soup)

        if not majors_and_degrees:
            thread_safe_log(logging.WARNING, f"No majors and degrees found for: {url}")
            majors_and_degrees = []  # Return empty list instead of failing

        # Create the JSON structure similar to existing Peterson data
        json_data = {
            "university_name": extracted_university_name,
            "majors_and_degrees": majors_and_degrees,
        }

        thread_safe_log(
            logging.INFO,
            f"Successfully scraped {extracted_university_name} with {len(majors_and_degrees)} categories",
        )

        # Return in the same format as existing Peterson data: {metadata: ..., json: ...}
        return {
            "metadata": {
                "sourceURL": url,
                "statusCode": response.status_code,
                "contentType": response.headers.get("content-type", ""),
            },
            "json": json_data,
        }

    except requests.exceptions.RequestException as e:
        thread_safe_log(logging.ERROR, f"Request error for {url}: {str(e)}")
        # Return empty majors and degrees instead of failing
        return {
            "metadata": {
                "error": f"Request error: {str(e)}",
                "sourceURL": url,
                "statusCode": 0,
                "contentType": "",
            },
            "json": {
                "university_name": university_name or "Unknown University",
                "majors_and_degrees": [],
            },
        }
    except Exception as e:
        thread_safe_log(logging.ERROR, f"Error scraping {url}: {str(e)}")
        # Return empty majors and degrees instead of failing
        return {
            "metadata": {
                "error": str(e),
                "sourceURL": url,
                "statusCode": 0,
                "contentType": "",
            },
            "json": {
                "university_name": university_name or "Unknown University",
                "majors_and_degrees": [],
            },
        }


def process_url_with_retries(
    url_info: dict, max_retries: int, output_dir: Path
) -> dict:
    """Process a single URL with retry logic and file saving"""
    url = url_info["url"]
    university_name = url_info["university_name"]

    # Retry logic for failed scrapes
    success = False
    result = None

    for attempt in range(max_retries):
        if attempt > 0:
            thread_safe_log(
                logging.INFO, f"Retry attempt {attempt} for: {university_name}"
            )

        # Scrape the URL
        result = scrape_university_courses(
            url=url,
            university_name=university_name,
        )

        # Check if scraping was successful (has json data and no error in metadata)
        if (
            result["json"] is not None
            and isinstance(result["json"], dict)
            and result["json"]
            and "error" not in result["metadata"]
        ):
            thread_safe_log(logging.INFO, f"Successfully scraped: {university_name}")

            # Save individual file using URL-based filename (like existing Peterson data structure)
            url_path = (
                url.replace("https://", "")
                .replace("http://", "")
                .replace("/", "_")
                .replace(":", "")
            )
            individual_file = output_dir / f"{url_path}.json"

            with open(individual_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            success = True
            break

        else:
            error_msg = result["metadata"].get("error", "Unknown error")
            if attempt < max_retries - 1:
                thread_safe_log(
                    logging.WARNING,
                    f"Attempt {attempt + 1} failed for {university_name}: {error_msg}",
                )
            else:
                # Final failure after all retries
                thread_safe_log(
                    logging.ERROR,
                    f"Failed to scrape after {max_retries} attempts: {university_name} - {error_msg}",
                )
                thread_safe_log(logging.ERROR, f"Failed URL: {url}")

    return {
        "url_info": url_info,
        "success": success,
        "result": result,
    }


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape Peterson URLs using BeautifulSoup with parallel processing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--max-urls",
        type=int,
        help="Maximum number of URLs to process (for testing)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries for failed scrapes",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/external/peterson_courses_data",
        help="Output directory for scraped data",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    logger.info(
        "Starting Peterson courses scraping with BeautifulSoup and parallel processing..."
    )
    logger.info(
        f"Configuration: max_urls={args.max_urls}, max_retries={args.max_retries}, max_workers={args.max_workers}"
    )

    # Create output directory
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load validation results to determine URLs to scrape
    validation_file = (
        PROJECT_ROOT / "data" / "cleaned" / "peterson_url_validation_results.json"
    )
    if not validation_file.exists():
        logger.error(f"Validation results file not found: {validation_file}")
        sys.exit(1)

    with open(validation_file) as f:
        results = json.load(f)

    results = pd.DataFrame(results)
    logger.info(f"Loaded {len(results)} validation results")

    # Filter URLs to scrape
    matched = results[results["Overall_Match"]]
    name_matched = results[results["Name_Match"] & ~results["Overall_Match"]]
    tmp = results[~results["Name_Match"] & ~results["Overall_Match"]]
    accepted = tmp[tmp["Location_Match"] & (tmp["Name_Similarity"] > 60)]
    rejected = tmp[~tmp["Location_Match"]]
    salvage = rejected[rejected["Name_Similarity"] > 90]

    to_scrape = pd.concat([matched, name_matched, accepted, salvage]).drop_duplicates(
        subset=["Scraped_Name", "Scraped_Location", "URL"]
    )

    # Create list of URLs with university names
    urls_to_process = []
    for _, row in to_scrape.iterrows():
        urls_to_process.append(
            {
                "url": row["URL"],
                "university_name": row["Scraped_Name"],
                "location": row["Scraped_Location"],
            }
        )

    logger.info(f"Total URLs to scrape: {len(urls_to_process)}")

    # Check for existing files and filter out already scraped URLs
    def get_existing_files():
        """Get set of URLs that have already been scraped successfully"""
        existing_files = set()
        if output_dir.exists():
            for file_path in output_dir.glob("*.json"):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)
                    # Check if it's a successful scrape (has json content)
                    if data.get("json") is not None:
                        # Get the original URL from metadata
                        metadata = data.get("metadata", {})
                        source_url = metadata.get("sourceURL")
                        if source_url:
                            existing_files.add(source_url)
                            logger.debug(f"Found existing file with URL: {source_url}")
                except (json.JSONDecodeError, KeyError):
                    # Skip malformed files
                    continue
        return existing_files

    existing_scraped_urls = get_existing_files()
    logger.info(f"Found {len(existing_scraped_urls)} already scraped URLs")

    # Filter out already scraped URLs
    original_count = len(urls_to_process)
    urls_to_process = [
        url_info
        for url_info in urls_to_process
        if url_info["url"] not in existing_scraped_urls
    ]
    skipped_count = original_count - len(urls_to_process)

    if skipped_count > 0:
        logger.info(f"Skipping {skipped_count} already scraped URLs")

    logger.info(f"Remaining URLs to scrape: {len(urls_to_process)}")

    # Apply URL limits
    if args.max_urls:
        urls_to_process = urls_to_process[: args.max_urls]
        logger.info(f"Limited to {len(urls_to_process)} URLs (--max-urls)")

    if len(urls_to_process) == 0:
        logger.info(
            "No URLs to process. All URLs have already been scraped or no URLs match criteria."
        )
        return

    # Process URLs with parallel workers
    successful_scrapes = 0
    failed_scrapes = 0
    failed_urls = []

    logger.info(
        f"Starting to scrape {len(urls_to_process)} URLs with {args.max_workers} parallel workers..."
    )

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(
                process_url_with_retries,
                url_info,
                args.max_retries,
                output_dir,
            ): url_info
            for url_info in urls_to_process
        }

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_url), 1):
            url_info = future_to_url[future]
            try:
                task_result = future.result()

                if task_result["success"]:
                    successful_scrapes += 1
                else:
                    failed_scrapes += 1
                    error_msg = task_result["result"]["metadata"].get(
                        "error", "Unknown error"
                    )
                    failed_urls.append(
                        {
                            "url": url_info["url"],
                            "university_name": url_info["university_name"],
                            "error": f"{error_msg} (after {args.max_retries} attempts)",
                        }
                    )

                # Log progress
                thread_safe_log(
                    logging.INFO,
                    f"Progress: {i}/{len(urls_to_process)} - Success: {successful_scrapes}, Failed: {failed_scrapes}",
                )

            except Exception as exc:
                failed_scrapes += 1
                thread_safe_log(
                    logging.ERROR,
                    f"Task generated an exception for {url_info['university_name']}: {exc}",
                )
                failed_urls.append(
                    {
                        "url": url_info["url"],
                        "university_name": url_info["university_name"],
                        "error": f"Task exception: {str(exc)}",
                    }
                )

    # Print summary
    logger.info("=" * 50)
    logger.info("SCRAPING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total URLs processed: {len(urls_to_process)}")
    logger.info(f"Successful scrapes: {successful_scrapes}")
    logger.info(f"Failed scrapes: {failed_scrapes}")
    logger.info(
        f"Success rate: {(successful_scrapes / len(urls_to_process) * 100):.1f}%"
    )
    logger.info(f"Files saved to: {output_dir}")

    # Log failed URLs summary
    if failed_urls:
        logger.info("=" * 50)
        logger.info("FAILED URLS SUMMARY")
        logger.info("=" * 50)
        for failed in failed_urls:
            logger.error(
                f"FAILED: {failed['university_name']} - {failed['url']} - Error: {failed['error']}"
            )

    logger.info(
        f"Total existing files (including previous runs): {len(existing_scraped_urls) + successful_scrapes}"
    )


if __name__ == "__main__":
    main()
