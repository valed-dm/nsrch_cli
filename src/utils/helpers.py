"""
Shared utility functions for the application.
"""
import asyncio
import random
from typing import List

# --- 1. IMPORT THE 'COOKIE' TYPE FROM PLAYWRIGHT ---
from playwright.async_api import Cookie

from src.core.logging_setup import log


async def human_sleep(a: float = 0.6, b: float = 1.6) -> None:
    """Asynchronously waits for a random duration to mimic human behavior."""
    t = random.uniform(a, b)
    log.debug(f"Sleeping for {t:.2f} seconds.")
    await asyncio.sleep(t)


# --- 2. UPDATE THE FUNCTION SIGNATURE ---
# The function now correctly states that it expects a list of Playwright Cookie objects.
def build_cookie_header(cookies: List[Cookie]) -> str:
    """Constructs a cookie header string from a list of Playwright cookies."""
    if not cookies:
        return ""
    # The rest of the logic works perfectly, as Cookie objects can be accessed like dicts.
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)
