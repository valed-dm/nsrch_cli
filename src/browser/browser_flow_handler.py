"""
Handles a complete search-solve-scrape workflow within a single
persistent Playwright browser session when a CAPTCHA is anticipated or detected.
"""

import random
from typing import Any
from typing import Dict
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from src.core.config import settings
from src.core.logging_setup import log
from src.ai.captcha_solver import solve_yandex_captcha
from src.scraping.search_parser import parse_with_selectors


async def run_full_browser_flow(
    engine_config: Dict[str, Any],
    query: str,
    proxy_pool: list[dict],
    initial_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handles the entire search flow within a browser, sequentially handling
    cookie banners and CAPTCHAs before parsing.
    """
    log.warning("Switching to full browser-based flow to handle potential CAPTCHA.")

    async with async_playwright() as p:
        browser_launch_args: Dict[str, Any] = {"headless": False}
        if proxy_pool:
            proxy_info = random.choice(proxy_pool)
            proxy = proxy_info["proxy"]
            browser_launch_args["proxy"] = {"server": proxy}
            log.info(
                f"Full browser flow using proxy (Score: {proxy_info['score']}): {proxy}"
            )

        browser = await p.chromium.launch(**browser_launch_args)
        context = await browser.new_context(user_agent=initial_state["user_agent"])
        page = await context.new_page()

        try:
            q_encoded = quote_plus(query)
            search_url = engine_config["search_url_template"].format(query=q_encoded)

            log.info(f"Navigating directly to search URL: {search_url}")
            await page.goto(search_url, wait_until="networkidle", timeout=60000)

            # --- FINAL, SEQUENTIAL WORKFLOW ---

            # STEP 1: Handle Cookie Banner First
            log.info("Checking for cookie consent banner...")
            for selector in engine_config.get("consent_button_selectors", []):
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=5000):
                        log.warning("Cookie consent banner detected. Clicking it.")
                        await button.click(delay=random.randint(100, 250))
                        # Wait for the page to react to the cookie click
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        log.info("Cookie banner handled.")
                        break
                except Exception:
                    log.debug(
                        f"Cookie button with selector '{selector}'"
                        f" not found, continuing."
                    )

            # STEP 2: Now, check for a CAPTCHA on the current page
            # We can check for the presence of the captcha button as our indicator
            captcha_button_locator = page.locator("#js-button")
            if await captcha_button_locator.count() > 0:
                log.warning("CAPTCHA form detected. Initiating solver...")
                is_solved = await solve_yandex_captcha(page)
                if not is_solved:
                    raise Exception(
                        "Failed to solve the CAPTCHA after handling cookies."
                    )
                log.info("CAPTCHA handled.")

            # STEP 3: We should now be on the results page. Parse it.
            log.success("All checks passed. Now parsing search results page...")
            await page.wait_for_selector("#search-result, #search", timeout=15000)

            html_content = await page.content()
            parsed_data = parse_with_selectors(html_content)

            await browser.close()
            return {"status": "success", "parsed_data": parsed_data}

        except Exception as e:
            log.error(
                f"An error occurred during the full browser flow:"
                f" {str(e).splitlines()[0]}"
            )
            if browser and browser.is_connected():

                failure_screenshot_path = (
                    settings.SCREENSHOT_DIR / "browser_flow_failure.png"
                )
                await page.screenshot(path=failure_screenshot_path)

                log.info(f"Saved browser flow failure screenshot "
                         f"{failure_screenshot_path}.")
                await browser.close()
            return {"status": "error", "message": str(e)}
