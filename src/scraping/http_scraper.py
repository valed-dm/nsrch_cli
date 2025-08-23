"""
Performs the actual search using fast, headless HTTP requests.

This module uses curl_cffi to impersonate a real browser's TLS fingerprint,
relying on the state (cookies, user-agent) extracted by the Playwright handler.
"""
import random
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import quote_plus

from curl_cffi.requests import AsyncSession
from curl_cffi.requests import errors

from src.core.config import settings, OUTPUT_DIR
from src.core.logging_setup import log
from src.utils.helpers import human_sleep


async def perform_http_search(
    query: str,
    engine_config: Dict[str, Any],
    state: Dict[str, Any],
    proxy_pool: List[Dict],
) -> Dict[str, Any]:
    """
    Executes a search query using a direct HTTP GET request with curl_cffi.

    Args:
        query: The user's search term.
        engine_config: Configuration for the target search engine.
        state: The session state (cookies, user-agent) from the warm-up phase.

    Returns:
        A dictionary indicating the outcome (success, captcha, or error) and
        containing the response HTML if successful.
    """
    q_encoded = quote_plus(query)
    search_url = engine_config["search_url_template"].format(query=q_encoded)

    headers = {
        "User-Agent": state["user_agent"],
        "Cookie": state["cookie_header"],
        "Referer": engine_config["base_url"] + "/",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8",
    }

    proxy_config = {}
    if proxy_pool:
        top_proxies = proxy_pool[: max(1, len(proxy_pool) // 4)]
        selected_proxy_info = random.choice(top_proxies)
        proxy_url = selected_proxy_info["proxy"]
        log.info(
            f"Using high-quality random proxy (Score:"
            f" {selected_proxy_info['score']}): {proxy_url}"
        )
        proxy_config = {"http": proxy_url, "https": proxy_url}

    if settings.PROXY_HOST and settings.PROXY_USER:
        proxy_url = (
            f"http://{settings.PROXY_USER}:{settings.PROXY_PASS}"
            f"@{settings.PROXY_HOST}:{settings.PROXY_PORT}"
        )
        proxy_config = {"http": proxy_url, "https": proxy_url}
        log.info(f"Using proxy for HTTP request: {settings.PROXY_HOST}")

    await human_sleep(0.8, 2.2)
    log.info(f"Performing HTTP search -> GET {search_url}")

    try:
        async with AsyncSession(
            proxies=proxy_config, verify=False, impersonate=settings.IMPERSONATE_TARGET
        ) as session:
            resp = await session.get(
                search_url, headers=headers, timeout=settings.REQUEST_TIMEOUT
            )

            log.info(f"HTTP response status: {resp.status_code}")
            html_content = resp.text

            # --- CAPTCHA Detection ---
            for keyword in engine_config.get("captcha_keywords", []):
                if keyword.lower() in html_content.lower():
                    log.warning(f"CAPTCHA detected with keyword: '{keyword}'")

                    # Save the CAPTCHA page for further analysis
                    filename = settings.CAPTCHAS_DIR / f"captcha_{
                    engine_config['name']}_{query.replace(' ', '_')
                    }.html"

                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    log.info(f"CAPTCHA page saved to {filename}")

                    return {
                        "status": "captcha",
                        "html_content": html_content,
                        "url": str(resp.url),
                    }

            # --- Success Case ---
            log.success("Search successful, no CAPTCHA detected.")
            filename = (
                settings.SUCCESS_DIR / f"success_{
                engine_config['name']}_{query.replace(' ', '_')
            }.html"
            )
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            log.info(f"Result page saved to {filename}")

            return {"status": "success", "html_content": html_content}

    except errors.RequestsError as e:
        log.error(f"An HTTP request error occurred for query '{query}': {e}")
        return {"status": "error", "message": str(e)}
