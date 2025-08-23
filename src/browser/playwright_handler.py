"""
Handles browser automation tasks using Playwright, specifically for
session warm-up and state extraction with robust, custom mobile emulation.
"""
import random
from typing import Any
from typing import Dict
from typing import List
from typing import TypedDict

from playwright.async_api import Error
from playwright.async_api import Geolocation
from playwright.async_api import async_playwright
from timezonefinder import TimezoneFinder

from src.core.config import settings
from src.core.logging_setup import log
from src.utils.helpers import build_cookie_header
from src.utils.helpers import human_sleep


tf = TimezoneFinder()

class MobileProfile(TypedDict):
    name: str
    user_agent: str
    viewport: Dict[str, int]
    device_scale_factor: float
    is_mobile: bool
    has_touch: bool
    geolocation: Geolocation
    permissions: List[str]
    default_browser_type: str


CUSTOM_MOBILE_PROFILES: List[MobileProfile] = [
    {
        "name": "Custom Android (Pixel 5)",
        "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                      "AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/90.0.4430.91 Mobile Safari/537.36",
        "viewport": {"width": 393, "height": 851},
        "device_scale_factor": 2.75,
        "is_mobile": True,
        "has_touch": True,
        "geolocation": {"longitude": 37.6173, "latitude": 55.7558},  # Moscow
        "permissions": ["geolocation"],
        "default_browser_type": "chromium"
    },
    {
        "name": "Custom iOS (iPhone 13 Pro)",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X)"
                      " AppleWebKit/605.1.15 (KHTML, like Gecko)"
                      " Version/15.5 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 390, "height": 844},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
        "geolocation": {"longitude": 12.4964, "latitude": 41.9028},  # Rome
        "permissions": ["geolocation"],
        "default_browser_type": "webkit"
    },
    {
        "name": "Custom Android (Galaxy S9+)",
        "user_agent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G965F Build/R16NW)"
                      " AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/65.0.3325.109 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 846},
        "device_scale_factor": 3.5,
        "is_mobile": True,
        "has_touch": True,
        "geolocation": {"longitude": 2.3522, "latitude": 48.8566},   # Paris
        "permissions": ["geolocation"],
        "default_browser_type": "chromium"
    }
]


async def warmup_session_and_get_state(
    engine_config: Dict[str, Any], proxy_pool: list[dict]
) -> Dict[str, Any]:
    """
    Launches a browser to warm up a session on a specific search engine.
    (Full docstring as before)
    """
    profile = random.choice(CUSTOM_MOBILE_PROFILES)
    log.info(
        f"Starting Playwright warm-up for {engine_config['name']}"
        f" using custom profile: {profile['name']}"
    )

    geo = profile.get("geolocation")
    timezone_id = "Europe/London"  # A sensible default
    if geo:
        found_timezone = tf.timezone_at(lng=geo["longitude"], lat=geo["latitude"])
        if found_timezone:
            timezone_id = found_timezone
            log.info(f"Dynamically set timezone to '{timezone_id}' based on geolocation.")

    async with async_playwright() as p:
        browser_launch_args: Dict[str, Any] = {"headless": True}

        if proxy_pool:
            best_proxy = proxy_pool[0]
            proxy_to_use = best_proxy["proxy"]
            log.info(f"Using BEST free proxy for warm-up (Score: {best_proxy['score']}): {proxy_to_use}")
            browser_launch_args["proxy"] = {"server": proxy_to_use}
        elif settings.PROXY_HOST and settings.PROXY_USER:
            proxy_to_use = f"http://{settings.PROXY_USER}:{settings.PROXY_PASS}@{settings.PROXY_HOST}:{settings.PROXY_PORT}"
            log.info(f"Using configured private proxy for warm-up: {proxy_to_use}")
            browser_launch_args["proxy"] = {"server": proxy_to_use}

        browser_engine = p[profile["default_browser_type"]]
        browser = await browser_engine.launch(**browser_launch_args)

        # --- THE FINAL, DEFINITIVE FIX ---
        # 1. Create a copy of the profile dictionary to avoid modifying the original.
        context_args = profile.copy()

        # 2. Remove the custom keys that are not valid Playwright arguments.
        del context_args["name"]
        del context_args["default_browser_type"]

        context = await browser.new_context(
            **context_args,
            locale="ru-RU",
            timezone_id=timezone_id  # Use the dynamic timezone
        )
        page = await context.new_page()

        try:
            log.info(f"Navigating to {engine_config['base_url']}...")
            await page.goto(
                engine_config["base_url"],
                wait_until="domcontentloaded",
                timeout=45000,
            )
            await human_sleep(1.5, 2.5)

            # --- Handle cookie consents ---
            for selector in engine_config.get("consent_button_selectors", []):
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        log.info("Consent button found. Clicking it.")
                        await button.click(delay=random.randint(50, 150))
                        await human_sleep(1.0, 2.0)
                        break
                except Error:
                    continue

            # --- Emulate realistic interaction ---
            log.info("Emulating human-like interaction (scrolls and taps)...")
            viewport = page.viewport_size
            if viewport:
                start_x = viewport["width"] / 2 + random.randint(-40, 40)
                start_y = viewport["height"] * 0.7 + random.randint(-50, 50)
                end_y = viewport["height"] * 0.3 + random.randint(-50, 50)
                await page.mouse.move(start_x, start_y)
                await page.mouse.down()
                await page.mouse.move(start_x, end_y, steps=5)
                await page.mouse.up()
                log.debug(f"Emulated a flick scroll from Y={start_y} to Y={end_y}.")

            await human_sleep(1.5, 3.0)

            # --- Extract state ---
            cookies = await context.cookies()
            cookie_header = build_cookie_header(cookies)
            log.success(f"Warm-up complete. Extracted {len(cookies)} cookies.")

            return {
                "success": True,
                "user_agent": profile["user_agent"],
                "cookie_header": cookie_header,
            }
        except Error as e:
            log.error(f"A Playwright error occurred during warm-up: {str(e).splitlines()[0]}")
            return {"success": False, "error": str(e)}
        finally:
            if browser.is_connected():
                await browser.close()
                log.info("Playwright session closed.")
