"""
Handles solving visual CAPTCHAs using Playwright and a multi-modal AI model.
"""

import random

from playwright.async_api import Error
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.core.config import settings
from src.core.logging_setup import log


async def solve_yandex_captcha(page: Page) -> bool:
    """
    Attempts to solve the Yandex "I'm not a robot" CAPTCHA on the given page.
    """
    log.warning("Yandex CAPTCHA detected. Initiating AI solver...")

    try:
        checkbox_button_locator = page.locator("#js-button")
        await checkbox_button_locator.wait_for(state="visible", timeout=15000)
        log.info("Found the CAPTCHA button. Clicking it...")

        await checkbox_button_locator.click(delay=random.randint(200, 400))

        # --- THE DEFINITIVE FIX: WAIT FOR URL CHANGE ---
        # A successful solve MUST navigate away from the captcha page to a URL
        # that contains '/search/'. We will wait up to 15 seconds for this.
        log.info("Waiting for successful navigation to search results page...")

        # The 'url' argument can be a glob pattern or a regex.
        await page.wait_for_url("**/search/**", timeout=15000)

        log.success("Navigation successful! CAPTCHA has been solved.")
        return True

    except PlaywrightTimeoutError:
        # This block will execute if the page URL does NOT change within the timeout.
        # This is the definitive sign of failure.
        log.error("Solver failed: Page did not navigate away from CAPTCHA after click.")

        captcha_screenshot_path = (settings.CAPTCHAS_DIR / "browser_flow_failure.png")
        await page.screenshot(path=captcha_screenshot_path)

        log.info("Saved failure screenshot to old_output/captcha_failure.png")
        return False

    except Error as e:
        log.error(
            f"A Playwright error occurred during CAPTCHA solving: "
            f"{str(e).splitlines()[0]}"
        )
        return False
    except Exception as e:
        log.error(
            f"An unexpected error occurred during CAPTCHA solving: "
            f"{str(e).splitlines()[0]}"
        )
        return False
