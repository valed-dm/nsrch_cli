"""
Handles visiting URLs from parsed data, interacting with the page,
and saving screenshots for demonstration purposes.
"""

import asyncio
from pathlib import Path
import random

from playwright.async_api import Error
from playwright.async_api import async_playwright

from src.core.config import settings
from src.core.logging_setup import log


async def visit_urls_and_screenshot(
    query: str, results: list[dict], proxy_pool: list[dict]
):
    """
    Launches a headed browser, visits each URL from the results,
    emulates human interaction, and saves a screenshot.

    Args:
        query: The original search query, used for naming the old_output folder.
        results: The list of parsed search results to visit.
        proxy_pool: The rated list of available proxies.
    """
    if not results:
        log.warning("No results to visit. Skipping screenshot step.")
        return

    log.info(f"--- Starting Demo: Visiting and Screenshotting {len(results)} URLs ---")

    # Create a unique, sanitized folder name for this query's screenshots
    query_slug = "".join(c for c in query.replace(" ", "_") if c.isalnum() or c == "_")
    output_dir = settings.SCREENSHOT_DIR / query_slug

    log.info(f"Screenshots will be saved in: {output_dir.resolve()}")

    async with async_playwright() as p:
        for i, result in enumerate(results, start=1):
            url = result.get("url")
            if not url:
                log.warning(f"[{i}/{len(results)}] Skipping result with no URL.")
                continue

            log.info(f"[{i}/{len(results)}] Preparing to visit: {url}")

            # --- Browser Launch Configuration ---
            # Run in headed mode for the demo to be visible.
            launch_options = {"headless": False}

            if proxy_pool:
                # Select a random proxy from the top tier (e.g., top 25% or top 5)
                top_proxies = proxy_pool[: max(1, len(proxy_pool) // 4)]
                proxy_info = random.choice(top_proxies)
                proxy = proxy_info["proxy"]
                launch_options["proxy"] = {"server": proxy}
                log.info(f"Using proxy (Score: {proxy_info['score']}): {proxy}")

            browser = None  # Initialize browser variable
            try:
                browser = await p.chromium.launch(**launch_options)
                context = await browser.new_context(
                    # Use a standard mobile profile for consistency
                    **p.devices["Pixel 5"],
                    locale="en-US",
                )
                page = await context.new_page()

                log.info("Navigating to page...")
                # Use a generous timeout for potentially slow sites/proxies
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)

                # --- Emulate Human Interaction ---
                log.info("Page loaded. Emulating user interaction...")
                # Wait for a moment to let the page settle
                await asyncio.sleep(random.uniform(2.0, 4.0))

                # Perform a series of random scrolls to simulate reading
                for _ in range(random.randint(1, 3)):
                    scroll_amount = random.randint(400, 800)
                    await page.mouse.wheel(0, scroll_amount)
                    log.debug(f"Scrolled down by {scroll_amount} pixels.")
                    await asyncio.sleep(random.uniform(1.0, 2.5))

                # Perform a random tap on the screen
                viewport_size = page.viewport_size
                if viewport_size:
                    tap_x = random.randint(
                        int(viewport_size["width"] * 0.2),
                        int(viewport_size["width"] * 0.8),
                    )
                    tap_y = random.randint(
                        int(viewport_size["height"] * 0.2),
                        int(viewport_size["height"] * 0.8),
                    )
                    await page.touchscreen.tap(tap_x, tap_y)
                    log.debug(f"Tapped at position ({tap_x}, {tap_y}).")

                await asyncio.sleep(random.uniform(1.5, 3.0))

                # --- Save Screenshot ---
                # Sanitize the URL to create a valid filename
                domain = url.split("//")[1].split("/")[0].replace(".", "_")

                screenshot_path = output_dir / f"{i}_{domain}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                log.success(f"Saved screenshot to {screenshot_path}")

            except Error as e:
                # Catch specific Playwright errors (like timeouts) and log them
                log.error(f"Failed to process {url}. Error: {str(e).splitlines()[0]}")
            except Exception as e:
                # Catch any other unexpected errors
                log.error(f"An unexpected error occurred for {url}: {e}")
            finally:
                if browser and browser.is_connected():
                    await browser.close()
                    log.info("Browser instance closed.")
