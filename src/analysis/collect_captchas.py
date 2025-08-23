import asyncio
import hashlib
import random
from urllib.parse import quote_plus

from curl_cffi.requests import AsyncSession, errors

from src.core.config import settings
from src.core.logging_setup import log
from src.utils.proxy_handler import build_rated_proxy_pool

SEARCH_QUERIES = [
    "latest tech news",
    "weather in tokyo",
    "python asyncio tutorial",
    "лучшие рецепты борща",
    "новости спорта",
    "купить билет на самолет",
]

CAPTCHA_COLLECTION_DIR = settings.CAPTCHAS_DIR

# A generic mobile user agent to use for requests
MOBILE_USER_AGENT = ("Mozilla/5.0 (Linux; Android 11; Pixel 5)"
                     " AppleWebKit/537.36 (KHTML, like Gecko)"
                     " Chrome/90.0.4430.91 Mobile Safari/537.36"
                     )


async def ping_yandex_for_captcha(proxy: dict):
    """
    Performs a single search attempt with a given proxy using curl_cffi,
    trying to get a CAPTCHA.
    """
    query = random.choice(SEARCH_QUERIES)
    q_encoded = quote_plus(query)
    search_url = f"https://yandex.ru/search/?text={q_encoded}"

    proxy_url = proxy["proxy"]
    proxy_config = {"http": proxy_url, "https": proxy_url}

    # Standard headers for a mobile browser
    headers = {
        "User-Agent": MOBILE_USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }

    try:
        log.info(f"Pinging with proxy {proxy_url} (Score: {proxy['score']})...")

        # --- THE CORRECTED IMPLEMENTATION ---
        # Create a new AsyncSession for each request to correctly set the proxy.
        async with AsyncSession(
            proxies=proxy_config, verify=False, impersonate=settings.IMPERSONATE_TARGET
        ) as session:
            resp = await session.get(
                search_url, headers=headers, timeout=settings.REQUEST_TIMEOUT
            )
        # --- END OF CORRECTION ---

        html_content = resp.text

        if "CheckboxCaptcha-Inner" in html_content or "I'm not a robot" in html_content:
            html_hash = hashlib.md5(html_content.encode()).hexdigest()
            file_path = CAPTCHA_COLLECTION_DIR / f"{html_hash}.html"

            if not file_path.exists():
                log.success(f"New unique CAPTCHA found. Saving to {file_path.name}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
            else:
                log.debug("Found a duplicate CAPTCHA. Skipping.")
        else:
            log.info("Request was successful (no CAPTCHA).")

    except errors.RequestsError as e:
        log.warning(
            f"Proxy {proxy_url} failed with curl_cffi error: {e.__class__.__name__}"
        )
    except Exception as e:
        log.error(f"An unexpected error occurred with proxy {proxy_url}: {e}")


async def main_collector_loop():
    """
    The main autonomous loop that runs continuously to collect CAPTCHAs.
    """
    log.info("--- Starting Nightly CAPTCHA Collector with curl_cffi ---")

    while True:
        log.info("--- Starting new collection cycle ---")
        proxy_pool = await build_rated_proxy_pool(fetch_limit=100, max_concurrent=50)

        if not proxy_pool:
            log.error("Failed to build a proxy pool. Waiting for 10 minutes.")
            await asyncio.sleep(600)
            continue

        # We no longer need a shared session object.
        # Use a semaphore to limit the number of concurrent pings.
        max_concurrent_pings = 25
        sem = asyncio.Semaphore(max_concurrent_pings)

        async def throttled_ping(proxy):
            async with sem:
                await ping_yandex_for_captcha(proxy)

        tasks = [throttled_ping(p) for p in proxy_pool]
        await asyncio.gather(*tasks)

        wait_time_minutes = random.randint(5, 15)
        log.info(
            f"Collection cycle complete. Waiting for {wait_time_minutes} minutes..."
        )
        await asyncio.sleep(wait_time_minutes * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main_collector_loop())
    except KeyboardInterrupt:
        log.info("\nCollector stopped by user.")
