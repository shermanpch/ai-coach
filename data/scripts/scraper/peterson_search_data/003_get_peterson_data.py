import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from dotenv import load_dotenv
from firecrawl import FirecrawlApp, JsonConfig

from models import ExtractSchema

load_dotenv()


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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "peterson_batch_scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Change to project root
os.chdir(PROJECT_ROOT)


def split_into_batches(urls: List[str], num_batches: int) -> List[List[str]]:
    """Split a list of URLs into a specified number of batches"""
    if num_batches <= 0:
        raise ValueError("Number of batches must be greater than 0")

    batch_size = len(urls) // num_batches
    remainder = len(urls) % num_batches

    batches = []
    start_idx = 0

    for i in range(num_batches):
        # Add one extra URL to the first 'remainder' batches
        current_batch_size = batch_size + (1 if i < remainder else 0)
        end_idx = start_idx + current_batch_size

        if start_idx < len(urls):
            batches.append(urls[start_idx:end_idx])

        start_idx = end_idx

    return batches


def submit_batch(
    app: FirecrawlApp,
    batch_urls: List[str],
    batch_num: int,
    json_config: JsonConfig,
):
    """Submit a single batch of URLs and return job info"""
    logger.info(f"Submitting Batch {batch_num} with {len(batch_urls)} URLs")

    # Start the batch job
    batch_job = app.async_batch_scrape_urls(
        batch_urls,
        formats=["json"],
        json_options=json_config,
    )

    logger.info(f"Batch {batch_num} submitted successfully! Job ID: {batch_job.id}")

    return {"batch_number": batch_num, "job_id": batch_job.id, "urls": batch_urls}


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Submit Peterson URLs to Firecrawl for batch scraping",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--num-batches",
        type=int,
        default=10,
        help="Number of batches to split URLs into",
    )

    parser.add_argument(
        "--max-urls",
        type=int,
        help="Maximum number of URLs to process (for testing)",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    logger.info("Starting Peterson batch scraper...")
    logger.info(f"Configuration: num_batches={args.num_batches}")

    # Load validation results
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

    list_of_urls = to_scrape["URL"].tolist()
    logger.info(f"Total URLs to scrape: {len(list_of_urls)}")

    # Apply URL limits
    if args.max_urls:
        list_of_urls = list_of_urls[: args.max_urls]
        to_scrape = to_scrape.head(args.max_urls)
        logger.info(f"Limited to {len(list_of_urls)} URLs (--max-urls)")

    # Split URLs into batches
    url_batches = split_into_batches(list_of_urls, args.num_batches)
    logger.info(
        f"Split into {len(url_batches)} batches (requested {args.num_batches} batches)"
    )

    # Initialize the FirecrawlApp
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FIRECRAWL_API_KEY environment variable not set")
        sys.exit(1)

    app = FirecrawlApp(api_key=api_key)

    # Configure JSON extraction
    json_config = JsonConfig(
        schema=ExtractSchema.model_json_schema(),
        mode="llm-extraction",
        pageOptions={"onlyMainContent": True},
    )

    # Submit all batches
    batch_jobs = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Submitting {len(url_batches)} batches to Firecrawl...")

    for i, batch_urls in enumerate(url_batches, 1):
        logger.info(f"Processing batch {i}/{len(url_batches)}")

        # Submit the batch
        job_info = submit_batch(app, batch_urls, i, json_config)
        batch_jobs.append(job_info)

    # Create URL to batch mapping
    url_to_batch = {}
    for job in batch_jobs:
        for url in job["urls"]:
            url_to_batch[url] = {
                "batch_id": job["job_id"],
                "batch_number": job["batch_number"],
            }

    # Add batch information to the dataframe
    to_scrape["batch_id"] = to_scrape["URL"].map(lambda x: url_to_batch[x]["batch_id"])
    to_scrape["batch_number"] = to_scrape["URL"].map(
        lambda x: url_to_batch[x]["batch_number"]
    )

    # Save the enhanced dataframe
    output_file = (
        PROJECT_ROOT
        / "data"
        / "cleaned"
        / f"peterson_urls_with_batch_ids_{timestamp}.csv"
    )
    to_scrape.to_csv(output_file, index=False)

    logger.info("All batches submitted successfully!")
    logger.info(f"Enhanced dataframe saved to: {output_file}")

    # Print summary
    logger.info("Batch Summary:")
    for job in batch_jobs:
        logger.info(
            f"  Batch {job['batch_number']}: {job['job_id']} ({len(job['urls'])} URLs)"
        )

    logger.info("NEXT STEPS:")
    logger.info("1. Go to your Firecrawl dashboard")
    logger.info("2. Look for the batch job IDs listed above")
    logger.info("3. Download the ZIP files for each completed batch")
    logger.info(
        f"4. Use the CSV file to match downloaded data with original URLs: {output_file}"
    )


if __name__ == "__main__":
    main()
