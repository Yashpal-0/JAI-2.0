"""
Dynamic company context for JAI system prompt.

Scrapes zerostic.com on startup and every 24 h.  Falls back to a hardcoded
About section when the cache is absent or stale.
"""
import json
import time
from pathlib import Path

_CACHE_PATH = Path(__file__).parent / "company_cache.json"
_CACHE_TTL = 24 * 3600  # seconds

_FALLBACK_ABOUT = """\
## About Zerostic
Zerostic is a software development company based in Surajkund, Faridabad, Haryana, India — \
the ultimate destination for businesses looking to create world-class mobile apps and websites. \
We are more than just a business; we are a passionate team dedicated to providing the best \
service and products to our customers.

**Services:** Android app development, iOS app development, Web application & website \
development, App Design, UX/UI design, Web Design.

**Notable products:**
- **FnO Bazar** — Stock market data visualization and analysis for investors and F&O traders \
(Android + Web platform). Zerostic is the dedicated technology partner behind FnO Bazar.
- **AppLab** — EdTech platform for aspiring Android developers: curated video lectures and \
an integrated in-app IDE to learn and build Android apps.
- **LOA (Legend Outdoor Advertising)** — Mobile app for a leading outdoor advertising agency \
with a distinguished position across India.
- **Zerostic Studio** — Client portal at studio.zerostic.com for managing projects, payments, \
invoices, contracts, and scheduled calls with the Zerostic team.
- **Zerostic Research** — Public research platform at research.zerostic.com for hosting and \
participating in academic and industry surveys ("Empowering Research Through Insights").

**Contact:** support@zerostic.com | +91 8076376175
**Instagram:** instagram.com/zerostic
**Careers & Internships:** zerostic.link/internship (applications via Typeform)
**Location:** Surajkund, Faridabad, Haryana, India"""


# ── Cache helpers ──────────────────────────────────────────────────────────────

def _load_cache() -> dict[str, Any] | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text())
        if time.time() - data.get("fetched_at", 0) > _CACHE_TTL:
            return None
        return data
    except Exception:
        return None


def _save_cache(about: str) -> None:
    try:
        _CACHE_PATH.write_text(
            json.dumps({"about_section": about, "fetched_at": time.time()}, ensure_ascii=False, indent=2)
        )
    except Exception as e:
        print(f"[company_context] Cache write failed: {e}")


# ── Public API ─────────────────────────────────────────────────────────────────

def get_company_context_str() -> str:
    """Return the About Zerostic section for the system prompt (cache or fallback)."""
    cache = _load_cache()
    if cache and cache.get("about_section"):
        return cache["about_section"]
    return _FALLBACK_ABOUT


def _extract_about_section(pages: list) -> str:
    """Build a structured About section, enriched with the live website tagline."""
    if not pages:
        return _FALLBACK_ABOUT

    first = pages[0]
    text = first.page_content if hasattr(first, "page_content") else first.get("content", "")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    # Look for the multi-word hero headline; zerostic.com splits it across short lines
    tagline = ""
    text_lower = text.lower()
    if "empowering" in text_lower and "digital" in text_lower:
        tagline = "Empowering Your Digital Experience"
    elif "empowering" in text_lower and "research" in text_lower:
        tagline = "Empowering Research Through Insights"

    about = "## About Zerostic\n"
    if tagline:
        about += f"{tagline}\n\n"

    about += """\
**Services:** Android app development, iOS app development, Web application & website \
development, App Design, UX/UI design, Web Design.

**Notable products:**
- **FnO Bazar** — Stock market data visualization and analysis for investors and F&O traders \
(Android + Web platform). Zerostic is the dedicated technology partner behind FnO Bazar.
- **AppLab** — EdTech platform for aspiring Android developers: curated video lectures and \
an integrated in-app IDE to learn and build Android apps.
- **LOA (Legend Outdoor Advertising)** — Mobile app for a leading outdoor advertising agency \
with a distinguished position across India.
- **Zerostic Studio** — Client portal at studio.zerostic.com for managing projects, payments, \
invoices, contracts, and scheduled calls with the Zerostic team.
- **Zerostic Research** — Public research platform at research.zerostic.com for hosting and \
participating in academic and industry surveys ("Empowering Research Through Insights").

**Contact:** support@zerostic.com | +91 8076376175
**Instagram:** instagram.com/zerostic
**Careers & Internships:** zerostic.link/internship (applications via Typeform)
**Location:** Surajkund, Faridabad, Haryana, India"""

    return about


async def refresh_company_context() -> str:
    """
    Scrape zerostic.com → embed into Chroma → update cache.
    Returns the new About section string.
    """
    import asyncio
    from rag.crawler import fetch_zerostic_pages
    from rag.ingest import ingest_from_pages
    from rag.pipeline import reset_retriever

    print("[company_context] Refreshing from zerostic.com…")
    pages = await fetch_zerostic_pages()
    about = _extract_about_section(pages) if pages else _FALLBACK_ABOUT

    if pages:
        # Run blocking Chroma/embedding work in a thread so the event loop stays free
        await asyncio.to_thread(ingest_from_pages, pages)
        reset_retriever()

    _save_cache(about)
    print(f"[company_context] Refresh complete — {len(pages)} page(s) ingested.")
    return about
