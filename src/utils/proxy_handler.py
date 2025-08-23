import asyncio
import random
import time
from typing import TypedDict, List

import httpx

from src.core.config import settings
from src.core.logging_setup import log


class ProxyResult(TypedDict):
    proxy: str
    latency: float
    score: float
    status: str


async def fetch_proxy_list(limit: int = 40) -> list[str]:
    """Fetches a list of free proxies using httpx."""
    try:
        async with httpx.AsyncClient(
            trust_env=False
        ) as client:  # trust_env=False for safety
            resp = await client.get(settings.PROXYSCRAPE_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            proxies_data = data.get("proxies", [])
            proxies = [f"http://{p['proxy']}" for p in proxies_data]
            return random.sample(proxies, k=min(limit, len(proxies)))
    except Exception as e:
        log.error(f"Failed to fetch proxy list with httpx: {repr(e)}")
        return []


async def check_proxy_with_httpx(
    proxy: str, sem: asyncio.Semaphore, retries: int
) -> ProxyResult:
    """Validates a single proxy by creating a dedicated httpx client for it."""
    async with sem:
        for _ in range(retries):
            start_time = time.monotonic()
            try:
                async with httpx.AsyncClient(proxy=proxy) as client:
                    resp = await client.get("https://httpbin.org/ip", timeout=7)

                if resp.status_code == 200:
                    latency = time.monotonic() - start_time
                    score = max(0.0, 100 - (latency * 20))
                    return {
                        "proxy": proxy,
                        "latency": latency,
                        "score": round(score, 2),
                        "status": "ok",
                    }
            except (httpx.RequestError, asyncio.TimeoutError):
                await asyncio.sleep(0.5)
                continue

    return {"proxy": proxy, "latency": float("inf"), "score": 0, "status": "failed"}


async def build_rated_proxy_pool(
    fetch_limit: int = 10, max_concurrent: int = 20, num_retries: int = 2
) -> List[ProxyResult]:
    """Builds a validated proxy pool using the correct httpx client-per-proxy pattern."""
    log.info(
        f"Building rated proxy pool (limit={fetch_limit}, concurrent={max_concurrent}, retries={num_retries})..."
    )
    raw_proxies = await fetch_proxy_list(limit=fetch_limit)
    if not raw_proxies:
        return []

    sem = asyncio.Semaphore(max_concurrent)

    tasks = [check_proxy_with_httpx(p, sem, num_retries) for p in raw_proxies]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_proxies: List[ProxyResult] = []
    for res in results:
        if isinstance(res, dict) and res.get("status") == "ok":
            valid_proxies.append(res)
        elif isinstance(res, Exception):
            log.warning(f"A proxy check task failed: {res}")

    if valid_proxies:
        valid_proxies.sort(key=lambda x: x["score"], reverse=True)
        log.success(
            f"Built a rated proxy pool with {len(valid_proxies)} valid proxies."
        )
    else:
        log.warning("Could not find any working free proxies.")

    return valid_proxies


# Test block
if __name__ == "__main__":
    async def main_test():
        proxies = await build_rated_proxy_pool()
        print("\n--- Top 5 Proxies ---")
        for proxy_info in proxies[:5]:
            print(proxy_info)
        print("---------------------")

    asyncio.run(main_test())
