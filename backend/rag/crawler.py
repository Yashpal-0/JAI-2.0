"""Async HTTP scraper for zerostic.com."""
import httpx
from bs4 import BeautifulSoup
from typing import Any

ZEROSTIC_URLS = ["https://www.zerostic.com"]

_HEADERS = {"User-Agent": "JAI/2.0 (+https://zerostic.com)"}


async def fetch_zerostic_pages() -> list[dict[str, Any]]:
    """Fetch all Zerostic pages and return cleaned text content."""
    pages: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for url in ZEROSTIC_URLS:
            try:
                resp = await client.get(url, headers=_HEADERS)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                title = soup.title.get_text(strip=True) if soup.title else url
                text = soup.get_text(separator="\n", strip=True)
                pages.append({"url": url, "title": title, "content": text})
                print(f"[crawler] Fetched {url} ({len(text)} chars)")
            except Exception as e:
                print(f"[crawler] Failed {url}: {e}")
    return pages
