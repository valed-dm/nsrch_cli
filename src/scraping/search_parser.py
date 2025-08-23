import asyncio

from bs4 import BeautifulSoup

from src.core.logging_setup import log


def parse_with_selectors(html_content: str) -> list[dict]:
    """
    Parses the Yandex SERP HTML using precise BeautifulSoup CSS selectors.
    This is fast, reliable, and does not require an LLM.
    """
    soup = BeautifulSoup(html_content, "lxml")
    results = []

    serp_items = soup.select("div.serp-item")
    log.info(f"Found {len(serp_items)} potential 'serp-item' blocks.")

    for item in serp_items:
        link_tag = item.select_one("a.OrganicTitle-Link")
        if link_tag:
            url = link_tag.get("href")
            title_tag = link_tag.select_one("span.OrganicTitleContentSpan")

            if url and title_tag:
                title = title_tag.get_text(separator=" ", strip=True)

                results.append({"title": title, "url": url})

    return results


async def async_parse_html(html):
    parsed_data = await asyncio.to_thread(parse_with_selectors, html)
    return parsed_data
