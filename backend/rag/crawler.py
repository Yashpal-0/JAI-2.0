"""
Async BFS crawler for Zerostic public web properties.

Strategy:
- BFS from seed URLs across all same-domain pages (no depth cap — exhaustive).
- At each page, discover links and enqueue unvisited same-domain URLs.
- Fetch up to MAX_CONCURRENT pages at a time to avoid hammering the server.
- Crawl allow-listed external Zerostic properties (public portions only).
- Skip URL patterns that indicate auth-gated content.

Auth-gated pages (login, dashboard, account) are intentionally skipped:
scraping them without credentials only returns a login redirect anyway,
and scraping with credentials would expose private client data.
"""
import asyncio
from collections import deque
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# ── Configuration ──────────────────────────────────────────────────────────────

# BFS seeds — full zerostic.com domain will be discovered from here
_SEED_URLS = [
    "https://www.zerostic.com",
]

# Extra Zerostic properties to include (public landing page only, not BFS'd)
_EXTRA_URLS = [
    "https://studio.zerostic.com",
]

# Domains to BFS crawl (follow all discovered subpages)
_CRAWL_DOMAINS = {"www.zerostic.com", "zerostic.com"}

# Path fragments that indicate auth-gated or irrelevant pages — skip
_AUTH_PATH_FRAGMENTS = {
    "/login", "/signin", "/signup", "/register",
    "/dashboard", "/account", "/profile", "/settings",
    "/admin", "/api/", "/oauth", "/auth/",
}

# Skip file extensions that aren't HTML pages
_SKIP_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                    ".pdf", ".zip", ".css", ".js", ".woff", ".woff2", ".ttf"}

MAX_CONCURRENT = 5   # simultaneous in-flight requests
MAX_PAGES = 100      # safety cap — zerostic.com is small but guard anyway

_HEADERS = {"User-Agent": "JAI/2.0 (+https://zerostic.com)"}

# ── Helpers ────────────────────────────────────────────────────────────────────

_INDEX_SUFFIXES = ("/index.html", "/index.htm", "/index.php")
_META_NAMES = frozenset((
    "description", "keywords", "og:description", "og:title",
    "twitter:description", "twitter:title",
))


def _normalise(url: str) -> str:
    """Strip fragment, trailing slash, common index filenames for dedup."""
    p = urlparse(url)
    path = p.path.rstrip("/")
    for suf in _INDEX_SUFFIXES:
        if path.endswith(suf):
            path = path[: -len(suf)]
            break
    return p._replace(path=path, fragment="", query="").geturl()


def _is_crawlable(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return False
    if p.netloc not in _CRAWL_DOMAINS:
        return False
    path_lower = p.path.lower()
    if any(frag in path_lower for frag in _AUTH_PATH_FRAGMENTS):
        return False
    if any(path_lower.endswith(ext) for ext in _SKIP_EXTENSIONS):
        return False
    return True


def _extract_links(base_url: str, soup: BeautifulSoup) -> list[str]:
    found = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(base_url, href)
        if _is_crawlable(absolute):
            found.append(_normalise(absolute))
    return list(dict.fromkeys(found))


def _extract_meta(soup: BeautifulSoup) -> str:
    parts = []
    for tag in soup.find_all("meta"):
        name = (tag.get("name") or tag.get("property") or "").lower()
        content = (tag.get("content") or "").strip()
        if name in _META_NAMES and content:
            parts.append(f"{name}: {content}")
    return "\n".join(parts)


async def _fetch_one(
    client: httpx.AsyncClient,
    url: str,
    follow_links: bool = True,
) -> tuple[dict[str, Any] | None, list[str]]:
    """
    Fetch one URL.
    Returns (page_dict_or_None, discovered_links).
    discovered_links is empty when follow_links=False.
    """
    try:
        resp = await client.get(url, headers=_HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = _extract_links(url, soup) if follow_links else []
        meta_text = _extract_meta(soup)
        for tag in soup(["script", "style", "noscript", "svg", "img"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else url
        body = soup.get_text(separator="\n", strip=True)
        # CSR pages: body is nearly empty — fall back to meta tags
        content = body if len(body) >= 200 else f"{body}\n\n[Meta]\n{meta_text}".strip()
        print(f"[crawler] {url} ({len(content)} chars)")
        return {"url": url, "title": title, "content": content}, links
    except Exception as e:
        print(f"[crawler] Failed {url}: {e}")
        return None, []


# ── Public entry point ─────────────────────────────────────────────────────────

async def fetch_zerostic_pages() -> list[dict[str, Any]]:
    """
    BFS crawl all public Zerostic pages.

    Starts from _SEED_URLS, follows every discovered same-domain link
    (skipping auth-gated paths), then fetches _EXTRA_URLS without further
    BFS (those are external properties where we only want the landing page).
    """
    visited: set[str] = set()
    queue: deque[str] = deque(_normalise(u) for u in _SEED_URLS)
    pages: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:

        # ── BFS over zerostic.com ──────────────────────────────────────────────
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_with_sem(url: str):
            async with semaphore:
                return await _fetch_one(client, url, follow_links=True)

        while queue and len(pages) < MAX_PAGES:
            # Drain the current wave concurrently
            wave = []
            while queue and len(wave) < MAX_CONCURRENT:
                url = queue.popleft()
                if url not in visited:
                    visited.add(url)
                    wave.append(url)

            if not wave:
                break

            results = await asyncio.gather(*[fetch_with_sem(u) for u in wave])
            for page, links in results:
                if page:
                    pages.append(page)
                for link in links:
                    if link not in visited:
                        queue.append(link)

        # ── Extra allow-listed external pages (landing only) ──────────────────
        extra_results = await asyncio.gather(
            *[_fetch_one(client, u, follow_links=False) for u in _EXTRA_URLS]
        )
        for page, _ in extra_results:
            if page and page["url"] not in {p["url"] for p in pages}:
                pages.append(page)

    print(f"[crawler] Total: {len(pages)} page(s) fetched")
    return pages
