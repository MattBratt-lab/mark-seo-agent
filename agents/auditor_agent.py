"""Cross-reference auditor: live site (Firecrawl) vs research ``clean_data`` → gap report."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT_DIR / "data" / "clean"
DEFAULT_SITE_URL = "https://www.dandbgaragedoors.com/"

load_dotenv(ROOT_DIR / ".env", override=False)

# Florida-ish city tokens to compare research vs live copy (extend as needed).
_CITY_HINTS = (
    "boca raton",
    "jupiter",
    "west palm beach",
    "palm beach",
    "delray beach",
    "boynton beach",
    "lake worth",
    "wellington",
    "royal palm beach",
    "stuart",
    "port st lucie",
    "fort lauderdale",
    "miami",
)


def _firecrawl_scrape(url: str) -> dict[str, Any]:
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set; cannot scrape live site.")

    base = (os.getenv("FIRECRAWL_BASE_URL") or "https://api.firecrawl.dev").rstrip("/") + "/"
    endpoint = urljoin(base, "v1/scrape")
    payload: dict[str, Any] = {
        "url": url,
        "formats": ["markdown", "html"],
        "onlyMainContent": False,
    }
    with httpx.Client(timeout=90.0) as client:
        r = client.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        body = r.json()
    if not isinstance(body, dict):
        return {"success": False, "error": "Unexpected scrape response", "raw": body}
    return body


def _extract_h1_meta(html: str) -> dict[str, Any]:
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    h1s = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip() for h in h1s]
    metas = re.findall(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
        html,
        flags=re.I,
    )
    og_titles = re.findall(
        r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']*)["\']',
        html,
        flags=re.I,
    )
    phones = re.findall(
        r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        re.sub(r"<[^>]+>", " ", html),
    )
    return {
        "h1_tags": [h for h in h1s if h],
        "meta_descriptions": metas[:5],
        "og_titles": og_titles[:5],
        "phone_candidates": list(dict.fromkeys(phones))[:8],
    }


def _live_text_blob(scrape: dict[str, Any]) -> str:
    data = scrape.get("data") or scrape.get("document") or {}
    if isinstance(data, dict):
        md = data.get("markdown") or ""
        html = data.get("html") or ""
        blob = f"{md}\n{html}".lower()
        if blob.strip():
            return blob
    md_top = str(scrape.get("markdown") or "")
    html_top = str(scrape.get("html") or "")
    return f"{md_top}\n{html_top}".lower()


def _research_blob(clean_data: dict[str, Any]) -> str:
    res = clean_data.get("result") if isinstance(clean_data.get("result"), dict) else clean_data
    parts = [
        str(res.get("cleaned_text", "")),
        str(res.get("summary", "")),
        json.dumps(clean_data, ensure_ascii=False)[:50_000],
    ]
    return "\n".join(parts).lower()


def _top_phrases(text: str, *, n: int = 25) -> list[tuple[str, int]]:
    tokens = re.findall(r"[a-z0-9][a-z0-9\s\-]{2,40}", text, flags=re.I)
    phrases: list[str] = []
    for t in tokens:
        t = t.strip().lower()
        if len(t) < 4 or t.isdigit():
            continue
        phrases.append(t)
    return Counter(phrases).most_common(n)


def _mentions_city(text: str, city: str) -> bool:
    c = city.strip().lower()
    return bool(c) and c in text


def _service_lexicon() -> list[str]:
    return [
        "impact rated",
        "hurricane",
        "high wind",
        "garage door repair",
        "spring replacement",
        "opener installation",
        "commercial garage",
        "emergency repair",
        "same day",
        "insulated door",
        "carriage house",
        "smart garage",
    ]


def build_gap_report(
    *,
    clean_data: dict[str, Any],
    city: str,
    site_url: str | None = None,
) -> dict[str, Any]:
    """Scrape live site via Firecrawl, compare to research clean_data, return gap report dict."""
    url = (site_url or os.getenv("AUDIT_SITE_URL") or DEFAULT_SITE_URL).strip()
    scrape = _firecrawl_scrape(url)
    data_block = scrape.get("data") if isinstance(scrape.get("data"), dict) else {}
    html = str(data_block.get("html") or "")
    live_meta = _extract_h1_meta(html)
    live_blob = _live_text_blob(scrape)
    research_blob = _research_blob(clean_data)

    research_cities = [c for c in _CITY_HINTS if c in research_blob]
    site_cities = [c for c in _CITY_HINTS if c in live_blob]

    services = _service_lexicon()
    missing_services = [s for s in services if s in research_blob and s not in live_blob]

    cities_missing_on_site = [c for c in research_cities if c not in live_blob]
    if city.strip().lower() and not _mentions_city(live_blob, city):
        if city.strip().lower() not in [x.lower() for x in cities_missing_on_site]:
            cities_missing_on_site.append(city.strip().lower())

    competitor_terms = [p for p, _ in _top_phrases(research_blob, n=40)]
    missing_kw = [p for p in competitor_terms[:15] if len(p) > 6 and p in research_blob and p not in live_blob]

    nap_notes: list[str] = []
    if live_meta.get("phone_candidates"):
        nap_notes.append(f"Detected phone-like strings on live page: {live_meta['phone_candidates'][:3]}")
    else:
        nap_notes.append("No obvious tel pattern on homepage HTML; verify NAP in footer/schema manually.")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "live_site_url": url,
        "scrape_success": bool(scrape.get("success", True) and data_block),
        "live_page": {
            "h1_tags": live_meta.get("h1_tags", []),
            "meta_descriptions": live_meta.get("meta_descriptions", []),
            "og_titles": live_meta.get("og_titles", []),
            "cities_detected_on_site": site_cities,
        },
        "research_context": {
            "target_city": city,
            "cities_detected_in_research": research_cities,
            "top_research_phrases": competitor_terms[:20],
        },
        "gaps": {
            "missing_keywords_vs_live_site": missing_kw[:25],
            "cities_in_research_not_emphasized_on_homepage": cities_missing_on_site,
            "services_missing_from_live_homepage_copy": missing_services,
            "thin_location_page_signals": [
                "Homepage-only audit: subpages not crawled; add /locations/* URLs to AUDIT_SITE_URL or a crawl job for thin-page detection."
            ],
            "nap_notes": nap_notes,
        },
    }


def write_gap_report(report: dict[str, Any], path: Path | None = None) -> Path:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    out = path or (CLEAN_DIR / "site_gaps.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def run_audit_and_save(
    clean_data: dict[str, Any],
    *,
    city: str,
    site_url: str | None = None,
) -> Path:
    """Build gap report and write ``/data/clean/site_gaps.json``."""
    report = build_gap_report(clean_data=clean_data, city=city, site_url=site_url)
    return write_gap_report(report)
