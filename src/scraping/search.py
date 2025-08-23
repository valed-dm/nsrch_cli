"""
This module contains the core SearchApp class that encapsulates the
entire search-and-scrape workflow.
"""

import asyncio

from src.browser.browser_flow_handler import run_full_browser_flow
from src.browser.playwright_handler import warmup_session_and_get_state
from src.core.config import settings
from src.core.logging_setup import log
from src.scraping.http_scraper import perform_http_search
from src.scraping.search_parser import parse_with_selectors
from src.utils.result_handler import process_successful_results


class SearchApp:
    """
    Manages the entire workflow for a single search query.
    """

    def __init__(self, query: str, engine_key: str, proxy_pool: list[dict]):
        self.query = query
        self.engine_key = engine_key
        self.proxy_pool = proxy_pool
        self.engine_config = settings.SEARCH_ENGINES[self.engine_key]
        self.state = {}  # Will hold browser state after warm-up

    async def _warmup_session(self) -> bool:
        """Performs the initial browser warm-up to get a valid state."""
        log.info("--- Phase 1: Browser Warm-up ---")
        self.state = await warmup_session_and_get_state(
            self.engine_config, self.proxy_pool
        )
        if not self.state.get("success"):
            log.error("Failed to warm up browser session. Cannot proceed.")
            return False
        log.success("Initial state extracted successfully.")
        return True

    async def _attempt_fast_scrape(self):
        """Attempts the fast, headless HTTP scraping method first."""
        log.info("--- Phase 2: Attempting Fast HTTP Scrape ---")
        return await perform_http_search(
            self.query, self.engine_config, self.state, self.proxy_pool
        )

    async def _handle_captcha_with_browser(self):
        """Handles a CAPTCHA by falling back to the robust, full-browser method."""
        log.warning("--- Phase 2b: Fallback to Full Browser Flow for CAPTCHA ---")
        browser_result = await run_full_browser_flow(
            self.engine_config, self.query, self.proxy_pool, self.state
        )

        if browser_result["status"] == "success":
            parsed_data = browser_result["parsed_data"]
            await process_successful_results(self.query, parsed_data, self.proxy_pool)
        else:
            log.error(f"Full browser flow failed: {browser_result['message']}")

    async def run(self):
        """Executes the entire search-and-scrape workflow."""
        log.info(
            f"Starting new search for '{self.query}' on {self.engine_config['name']}..."
        )

        if not await self._warmup_session():
            return

        search_result = await self._attempt_fast_scrape()

        if search_result["status"] == "success":
            log.info("Fast scrape successful. Processing results...")
            html = search_result["html_content"]
            parsed_data = await asyncio.to_thread(parse_with_selectors, html)
            await process_successful_results(self.query, parsed_data, self.proxy_pool)

        elif search_result["status"] == "captcha":
            await self._handle_captcha_with_browser()

        elif search_result["status"] == "error":
            log.error(f"The search failed due to an error: {search_result['message']}")

        log.info(f"--- Workflow for query '{self.query}' complete. ---")
