"""
Handles the processing of successfully parsed search results,
including displaying, saving, and triggering follow-up actions.
"""

import typer

from src.core.logging_setup import log
from src.utils.data_saver import save_to_csv
from src.browser.page_interactor import visit_urls_and_screenshot


async def process_successful_results(
    query: str, parsed_data: list[dict], proxy_pool: list[dict]
):
    """
    Orchestrates the handling of parsed search results.

    This function will:
    1. Display the top 10 results to the console.
    2. Save the top 10 results to a CSV file.
    3. Trigger the browser session to visit and screenshot the results.

    Args:
        query: The original search query.
        parsed_data: The list of dictionaries from the parser.
        proxy_pool: The rated list of available proxies for the screenshotter.
    """
    if not parsed_data:
        log.warning("No data was parsed. Nothing to process.")
        return

    # --- 1. Display Results in Console ---
    log.info("--- Parsed Search Results ---")
    results_to_display = parsed_data[:10]
    results_table = []
    for i, result in enumerate(results_to_display, start=1):
        title = result.get("title", "N/A")
        url = result.get("url", "N/A")
        results_table.append(f"{i}. {title}\n   -> {url}\n")

    typer.echo("".join(results_table))
    log.info("-----------------------------")

    # --- 2. Save to CSV ---
    # The save_to_csv function already handles the limit of 10
    save_to_csv(query, parsed_data)

    # --- 3. Visit and Screenshot URLs ---
    # We'll visit the same top 10 results we displayed
    await visit_urls_and_screenshot(query, results_to_display, proxy_pool)
