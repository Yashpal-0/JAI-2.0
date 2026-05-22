"""
Async Playwright BFS crawler for Zerostic public web properties.

Returns LangChain Document objects — plug directly into the LangChain
text-splitter → embeddings → Chroma pipeline with no conversion step.

Uses a real Chromium browser so any JS framework (React, Next.js, Vue,
Angular, Svelte, …) renders fully before text/link extraction.
Network-idle wait catches Firestore / REST data fetches before scraping.
"""
import asyncio
from collections import deque
from urllib.parse import urljoin, urlparse

from langchain_core.documents import Document
from playwright.async_api import async_playwright, Browser, Page

# ── Configuration ──────────────────────────────────────────────────────────────

_SEED_URLS = [
    "https://www.zerostic.com",
    "https://research.zerostic.com",
]

# Public landing pages only — no BFS (CSR apps with auth-gated interiors)
_EXTRA_URLS = [
    "https://studio.zerostic.com",
]

# Domains where all discovered subpages are BFS-crawled
_CRAWL_DOMAINS = {"www.zerostic.com", "zerostic.com", "research.zerostic.com"}

# Path fragments that signal auth-gated content — skip automatically
_AUTH_PATH_FRAGMENTS = {
    "/login", "/signin", "/signup", "/register",
    "/dashboard", "/account", "/profile", "/settings",
    "/admin", "/api/", "/oauth", "/auth/",
}

_SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".pdf", ".zip", ".css", ".js", ".woff", ".woff2", ".ttf",
}

# Per-domain: CSS selector to wait for before extracting content.
# Use when the page loads dynamic data (Firestore, REST) after networkidle.
_DYNAMIC_WAIT_SELECTORS: dict[str, str] = {
    "research.zerostic.com": "a[href*='/surveys/']",
}

_CHROME_EXECUTABLE = "/usr/bin/google-chrome"
MAX_CONCURRENT = 3
MAX_PAGES = 100

# ── URL helpers ────────────────────────────────────────────────────────────────

_INDEX_SUFFIXES = ("/index.html", "/index.htm", "/index.php")


def _normalise(url: str) -> str:
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


# ── Page fetch → LangChain Document ───────────────────────────────────────────

async def _fetch_page(
    browser: Browser,
    url: str,
    follow_links: bool = True,
) -> tuple[Document | None, list[str]]:
    """
    Render url with Playwright, extract content as a LangChain Document.
    Returns (Document | None, discovered_links).
    """
    page: Page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        # Wait for network to settle (REST / Firestore data fetches)
        try:
            await page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass

        # Per-domain selector wait for late-loading dynamic content
        domain = urlparse(url).netloc
        if domain in _DYNAMIC_WAIT_SELECTORS:
            try:
                await page.wait_for_selector(
                    _DYNAMIC_WAIT_SELECTORS[domain], timeout=10_000
                )
            except Exception:
                pass

        # Clone body, strip noise, extract ALL text (including off-screen sections)
        text: str = await page.evaluate("""() => {
            const clone = document.body.cloneNode(true);
            clone.querySelectorAll(
                'script, style, noscript, svg, link, meta, iframe'
            ).forEach(el => el.remove());
            return clone.textContent;
        }""")
        text = " ".join(text.split())

        title: str = await page.title()

        # If body is sparse, supplement with meta description
        meta_desc: str = await page.evaluate(
            "() => (document.querySelector('meta[name=description]') || {}).content || ''"
        )
        if len(text) < 200 and meta_desc:
            text = f"{text} [Meta description: {meta_desc}]".strip()

        doc = Document(
            page_content=text,
            metadata={"source": url, "title": title, "web_scraped": True},
        )

        # Discover links from the rendered DOM (catches React-router hrefs)
        links: list[str] = []
        if follow_links:
            raw: list[str] = await page.evaluate(
                "() => [...document.querySelectorAll('a[href]')].map(a => a.href)"
            )
            for href in raw:
                if href and not href.startswith(("javascript:", "mailto:", "tel:", "#")):
                    absolute = urljoin(url, href)
                    if _is_crawlable(absolute):
                        links.append(_normalise(absolute))
            links = list(dict.fromkeys(links))

        print(f"[crawler] {url} ({len(text)} chars, {len(links)} links)")
        return doc, links

    except Exception as e:
        print(f"[crawler] Failed {url}: {e}")
        return None, []
    finally:
        await page.close()


# ── Public entry point ─────────────────────────────────────────────────────────

async def fetch_zerostic_pages() -> list[Document]:
    """
    BFS crawl all public Zerostic pages using headless Chromium.
    Returns LangChain Document objects ready for the splitter → Chroma pipeline.
    Handles any JS framework — React, Next.js, Vue, Angular, etc.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path=_CHROME_EXECUTABLE,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            visited: set[str] = set()
            queue: deque[str] = deque(_normalise(u) for u in _SEED_URLS)
            docs: list[Document] = []
            semaphore = asyncio.Semaphore(MAX_CONCURRENT)

            async def fetch_sem(url: str, follow: bool = True):
                async with semaphore:
                    return await _fetch_page(browser, url, follow_links=follow)

            # ── BFS over all crawlable domains ─────────────────────────────────
            while queue and len(docs) < MAX_PAGES:
                wave: list[str] = []
                while queue and len(wave) < MAX_CONCURRENT:
                    url = queue.popleft()
                    if url not in visited:
                        visited.add(url)
                        wave.append(url)
                if not wave:
                    break

                results = await asyncio.gather(*[fetch_sem(u) for u in wave])
                for doc, links in results:
                    if doc:
                        docs.append(doc)
                    for link in links:
                        if link not in visited:
                            queue.append(link)

            # ── Extra properties: public landing only ──────────────────────────
            visited_urls = {d.metadata["source"] for d in docs}
            extra = await asyncio.gather(
                *[fetch_sem(u, follow=False) for u in _EXTRA_URLS]
            )
            for doc, _ in extra:
                if doc and doc.metadata["source"] not in visited_urls:
                    docs.append(doc)

        finally:
            await browser.close()

    print(f"[crawler] Total: {len(docs)} document(s) fetched")
    return docs
