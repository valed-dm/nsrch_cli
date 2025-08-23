"""
Handles saving parsed search result data to a persistent format (CSV).
"""

import csv
from datetime import datetime

from src.core.config import OUTPUT_DIR
from src.core.logging_setup import log


OUTPUT_FILE = OUTPUT_DIR / "search_results.csv"
HEADERS = ["timestamp", "query", "title", "url"]


def save_to_csv(query: str, parsed_data: list[dict]):
    """
    Appends a list of parsed search results (up to a limit of 10)
    to a central CSV file.

    Creates the file and writes the header if it doesn't exist.

    Args:
        query: The search query that generated these results.
        parsed_data: A list of dictionaries, each with 'title' and 'url'.
    """
    records_to_save = parsed_data[:10]
    log.info(f"Saving {len(records_to_save)} results (limit 10) to {OUTPUT_FILE}...")

    try:
        file_exists = OUTPUT_FILE.exists()
        with open(OUTPUT_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)

            if not file_exists:
                writer.writeheader()

            timestamp = datetime.now().isoformat()

            for result in records_to_save:
                row = {
                    "timestamp": timestamp,
                    "query": query,
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                }
                writer.writerow(row)

        log.success("Successfully saved results to CSV.")

    except IOError as e:
        log.error(f"Failed to write to CSV file. Error: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred during CSV saving: {e}")
