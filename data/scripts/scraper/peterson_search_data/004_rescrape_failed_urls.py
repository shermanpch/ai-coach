import json
import os
import sys
from typing import List

from dotenv import load_dotenv
from firecrawl import FirecrawlApp, JsonConfig

from models import ExtractSchema
from projectutils.env import setup_project_environment
from projectutils.logger import setup_logger

load_dotenv()

# Call setup at the module level
PROJECT_ROOT, _ = setup_project_environment()

# Set up logging using the new utility
logger = setup_logger(__file__)

# Change to project root
os.chdir(PROJECT_ROOT)


def find_failed_files() -> List[str]:
    """Find files that are missing the json key and extract their URLs"""
    logger.info("Scanning for files missing 'json' key...")

    # Define the Peterson data directory
    peterson_data_dir = PROJECT_ROOT / "data" / "external" / "peterson_data"

    if not peterson_data_dir.exists():
        logger.error(f"Peterson data directory not found: {peterson_data_dir}")
        sys.exit(1)

    # Find all JSON files in the Peterson data directory
    json_files = list(peterson_data_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files to check")

    failed_urls = []

    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            # Check if json key is missing
            if "json" not in data:
                # Extract URL from metadata
                if "metadata" in data and "sourceURL" in data["metadata"]:
                    url = data["metadata"]["sourceURL"]
                    failed_urls.append(url)
                    logger.info(f"Found failed file: {json_file.name} -> {url}")
                else:
                    logger.warning(
                        f"File {json_file.name} missing json key but no sourceURL found"
                    )

        except Exception as e:
            logger.error(f"Error reading {json_file.name}: {e}")

    logger.info(f"Found {len(failed_urls)} URLs that need to be re-scraped")
    return failed_urls


def scrape_urls(urls: List[str]):
    """Scrape the failed URLs using Firecrawl"""
    if not urls:
        logger.info("No URLs to scrape")
        return

    logger.info(f"Starting re-scraping of {len(urls)} URLs...")

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

    # Submit batch job for failed URLs
    logger.info(f"Submitting batch job for {len(urls)} failed URLs")

    batch_job = app.async_batch_scrape_urls(
        urls,
        formats=["json"],
        json_options=json_config,
    )

    logger.info(f"Batch job submitted successfully! Job ID: {batch_job.id}")

    # Save the job info and URLs for reference
    output_dir = PROJECT_ROOT / "data" / "cleaned"
    output_dir.mkdir(parents=True, exist_ok=True)

    job_info = {
        "job_id": batch_job.id,
        "urls": urls,
        "total_urls": len(urls),
        "description": "Re-scraping URLs that were missing json key",
    }

    job_file = output_dir / "failed_urls_rescrape_job.json"
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job_info, f, indent=2)

    logger.info(f"Job information saved to: {job_file}")

    return batch_job.id


def main():
    """Main function to orchestrate the re-scraping process"""
    logger.info("Failed URLs Re-scraper - Starting...")

    # Find files missing json key and extract URLs
    failed_urls = find_failed_files()

    if not failed_urls:
        logger.info("No failed URLs found - all files have json key")
        return

    # Print the URLs for user reference
    logger.info("URLs to be re-scraped:")
    for i, url in enumerate(failed_urls, 1):
        logger.info(f"  {i}. {url}")

    # Scrape the failed URLs
    job_id = scrape_urls(failed_urls)

    logger.info("NEXT STEPS:")
    logger.info("1. Go to your Firecrawl dashboard")
    logger.info(f"2. Look for batch job ID: {job_id}")
    logger.info("3. Download the ZIP file when the job completes")
    logger.info("4. Extract the new JSON files to replace the failed ones")
    logger.info("5. Re-run the cleaning script (004_clean_peterson_data.py)")

    logger.info("Failed URLs Re-scraper - Complete!")


if __name__ == "__main__":
    main()
