import argparse
import json
import logging
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv
from firecrawl import FirecrawlApp, JsonConfig
from pydantic import BaseModel, Field

from models import MajorCategory

load_dotenv()


class UniversityCoursesSchema(BaseModel):
    """Simplified schema for extracting only university name and majors/degrees"""

    university_name: str = Field(
        ...,
        description="Name of the university, e.g. 'Harvard University', 'Ohio University', 'Georgia Institute of Technology'",
    )
    majors_and_degrees: List[MajorCategory]


def get_git_root():
    """Get the root directory of the git repository"""
    try:
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .strip()
            .decode("utf-8")
        )
        return Path(git_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Get the project root using git
PROJECT_ROOT = get_git_root()
if PROJECT_ROOT is None:
    print("Error: Not in a git repository or git not found")
    sys.exit(1)

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Set up thread-safe logging
script_name = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [Thread-%(thread)d] - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"{script_name}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Thread-safe logging lock
log_lock = threading.Lock()

# Change to project root
os.chdir(PROJECT_ROOT)


def thread_safe_log(level, message):
    """Thread-safe logging function"""
    with log_lock:
        logger.log(level, message)


def scrape_university_courses(
    app: FirecrawlApp,
    url: str,
    university_name: str = None,
) -> Dict[str, Any]:
    """Scrape a single university URL using actions to handle dynamic content with fallback for missing buttons"""
    try:
        thread_safe_log(logging.INFO, f"Scraping: {url}")

        # Use scrape endpoint with actions to click "See More" button and JSON extraction
        json_config = JsonConfig(schema=UniversityCoursesSchema.model_json_schema())

        # First try with "See More" button click
        try:
            scrape_result = app.scrape_url(
                url,
                formats=["json"],
                json_options=json_config,
                only_main_content=True,
                actions=[
                    {"type": "wait", "milliseconds": 3000},
                    {"type": "click", "selector": "#rm-more_1"},
                    {"type": "wait", "milliseconds": 1000},
                    {"type": "scrape"},
                ],
                timeout=80000,
            )

            if scrape_result.success:
                thread_safe_log(
                    logging.INFO, f"Successfully scraped with 'See More' click: {url}"
                )
                json_content = scrape_result.json if scrape_result.json else {}
                metadata = scrape_result.metadata if scrape_result.metadata else {}
                return {
                    "metadata": metadata,
                    "json": json_content,
                }
        except Exception as e:
            thread_safe_log(
                logging.WARNING,
                f"Failed to scrape with 'See More' click for {url}: {str(e)}",
            )

        # Fallback: scrape without clicking the button
        thread_safe_log(
            logging.INFO,
            f"Attempting fallback scrape without 'See More' button for: {url}",
        )
        scrape_result = app.scrape_url(
            url,
            formats=["json"],
            json_options=json_config,
            only_main_content=True,
            actions=[
                {"type": "wait", "milliseconds": 3000},
                {"type": "scrape"},
            ],
            timeout=80000,
        )

        if not scrape_result.success:
            thread_safe_log(logging.ERROR, f"Failed to scrape {url}: {scrape_result}")
            return {
                "metadata": {"error": "Scrape failed", "sourceURL": url},
                "json": None,
            }

        # Access data directly from ScrapeResponse attributes
        json_content = scrape_result.json if scrape_result.json else {}
        metadata = scrape_result.metadata if scrape_result.metadata else {}

        thread_safe_log(
            logging.INFO, f"Successfully scraped with fallback method: {url}"
        )
        # Return in the same format as existing Peterson data: {metadata: ..., json: ...}
        return {
            "metadata": metadata,
            "json": json_content,
        }

    except Exception as e:
        thread_safe_log(logging.ERROR, f"Error scraping {url}: {str(e)}")
        return {
            "metadata": {"error": str(e), "sourceURL": url},
            "json": None,
        }


def process_url_with_retries(
    app: FirecrawlApp, url_info: dict, max_retries: int, output_dir: Path
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
            app=app,
            url=url,
            university_name=university_name,
        )

        # Check if scraping was successful (has json data)
        if (
            result["json"] is not None
            and isinstance(result["json"], dict)
            and result["json"]
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

            with open(individual_file, "w") as f:
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
        description="Scrape Peterson URLs using Firecrawl scrape endpoint with parallel processing",
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
        default=2,
        help="Maximum number of parallel workers (browsers)",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    logger.info("Starting Peterson courses scraping with parallel processing...")
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
                    with open(file_path) as f:
                        data = json.load(f)
                    # Check if it's a successful scrape (has json content)
                    if data.get("json") is not None:
                        # Get the original URL from metadata instead of reconstructing from filename
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

    # Initialize the FirecrawlApp
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY environment variable not set")
        sys.exit(1)

    # Process URLs with parallel workers
    successful_scrapes = 0
    failed_scrapes = 0
    failed_urls = []

    logger.info(
        f"Starting to scrape {len(urls_to_process)} URLs with {args.max_workers} parallel workers..."
    )

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Create a FirecrawlApp instance for each worker thread
        def create_worker_task(url_info):
            # Each thread gets its own FirecrawlApp instance
            worker_app = FirecrawlApp(api_key=api_key)
            return executor.submit(
                process_url_with_retries,
                worker_app,
                url_info,
                args.max_retries,
                output_dir,
            )

        # Submit all tasks
        future_to_url = {
            create_worker_task(url_info): url_info for url_info in urls_to_process
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
