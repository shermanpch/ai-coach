#!/usr/bin/env python3
"""
Simple script to list available data categories from the GOSA website.
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data"


def parse_categories():
    """Parse and list all available data categories."""
    try:
        response = requests.get(BASE_URL, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        categories = set()
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
                if len(cells) >= 3:
                    category_name = cells[0].get_text(strip=True)

                    # Skip header rows, empty categories, and retired items
                    if (
                        not category_name
                        or category_name.upper()
                        in ["DATA CATEGORY", "RETIRED REPORTING"]
                        or "(Retired)" in category_name
                    ):
                        continue

                    # Check if there are data file links in the download cell
                    download_cell = cells[2]
                    links = download_cell.find_all("a", href=True)
                    has_data_files = any(
                        link["href"].endswith((".csv", ".xls", ".xlsx", ".zip"))
                        for link in links
                    )

                    if has_data_files:
                        categories.add(category_name)

        return sorted(categories)

    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    print("Available Data Categories from GOSA:")
    print("=" * 50)

    categories = parse_categories()

    for i, category in enumerate(categories, 1):
        print(f"{i:2d}. {category}")

    print(f"\nTotal: {len(categories)} categories available")
