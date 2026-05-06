"""Cross-reference auditor: live site (Firecrawl) vs research.

- LangGraph: single-page scrape + ``clean_data`` → ``data/clean/site_gaps.json``.
- Priority One CLI (``python agents/auditor_agent.py``): Firecrawl SDK crawl + Boca gap Markdown.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT_DIR / "data" / "clean"
RAW_DIR = ROOT_DIR / "data" / "raw"
DEFAULT_SITE_URL = "https://www.dandbgaragedoors.com/"
DEFAULT_RESEARCH_JSON = ROOT_DIR / ".firecrawl" / "research-boca-raton.json"
BOCA_PAGE_FRAGMENT = "locations/boca-raton"
GAP_MARKDOWN_PATH = CLEAN_DIR / "site_gap_analysis.md"
WORKFLOW_STATE_PATH = ROOT_DIR / "docs" / "workflow_state.md"

load_dotenv(ROOT_DIR / ".env", override=False)

# Curated Boca-area entities and hooks to compare against competitor "blueprint" copy.
_BOCA_LOCAL_ENTITIES = (
    "mizner park",
    "sandalfoot cove",
    "boca del mar",
    "spanish river",
    "east boca",
    "west boca",
    "royal palm yacht",
    "town center mall",
    "fau",
    "spanish river park",
)
_CONVERSION_PATTERNS = (
    ("24/7", "24/7 availability messaging"),
    ("24-hour", "24-hour / emergency framing"),
    ("emergency", "Emergency repair positioning"),
    ("same day", "Same-day service claim"),
    ("tune-up", "Tune-up / maintenance special"),
    ("$69", "$69-style tune-up offer"),
    ("tel:", "Click-to-call tel: link"),
)
_BRAND_ENTITY_CHECKS = (
    ("clopay", "Clopay doors / collections"),
    ("liftmaster", "LiftMaster openers"),
    ("hurricane-rated", "Hurricane / wind-load door framing"),
    ("impact rated", "Impact-rated door language"),
)
_TECH_BIO_SIGNALS = (
    "technician",
    "our team",
    "meet the",
    "certified",
    "installer",
    "trained professional",
)

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


_JUNK_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
    "were", "have", "has", "been", "will", "can", "our", "your", "their",
    "all", "more", "also", "very", "just", "not", "but", "about", "they",
    "you", "we", "it", "its", "be", "by", "at", "in", "on", "of", "to",
    # API/JSON noise
    "https", "http", "www", "com", "html", "json", "source", "snippet",
    "title", "description", "url", "null", "true", "false", "data", "type",
    "text", "list", "items", "results", "result", "object", "array",
    # generic SEO noise
    "click", "here", "read", "view", "more", "see", "get", "best",
    "yelp", "facebook", "google", "map", "maps", "reviews", "rating",
}


def _top_phrases(text: str, *, n: int = 25) -> list[tuple[str, int]]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    words = [w for w in words if w not in _JUNK_WORDS]

    bigrams: Counter = Counter()
    trigrams: Counter = Counter()
    for i in range(len(words) - 1):
        bigrams[f"{words[i]} {words[i+1]}"] += 1
    for i in range(len(words) - 2):
        trigrams[f"{words[i]} {words[i+1]} {words[i+2]}"] += 1

    results: list[tuple[str, int]] = []
    seen: set[str] = set()
    for phrase, count in trigrams.most_common(n * 2):
        if count >= 2:
            results.append((phrase, count))
            for w in phrase.split():
                seen.add(w)
    for phrase, count in bigrams.most_common(n * 2):
        if count >= 2 and not any(phrase in r[0] for r in results):
            results.append((phrase, count))
    results.sort(key=lambda x: -x[1])
    return results[:n]


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


_COMPETITOR_SERVICES = (
    ("garage door repair", "Garage Door Repair"),
    ("garage door installation", "Garage Door Installation"),
    ("spring replacement", "Spring Replacement"),
    ("torsion spring", "Torsion Spring"),
    ("extension spring", "Extension Spring"),
    ("cable repair", "Cable Repair / Replacement"),
    ("opener installation", "Opener Installation"),
    ("opener repair", "Opener Repair"),
    ("panel replacement", "Panel Replacement"),
    ("off track", "Off-Track Door Fix"),
    ("tune-up", "Tune-Up / Maintenance"),
    ("new garage door", "New Door Sales"),
    ("commercial garage", "Commercial Service"),
    ("emergency repair", "Emergency Repair"),
    ("hurricane", "Hurricane / Impact Doors"),
    ("insulated door", "Insulated Doors"),
    ("carriage house", "Carriage House Doors"),
    ("smart garage", "Smart / WiFi Opener"),
    ("keypad", "Keypad / Remote Entry"),
    ("weatherstripping", "Weather Seal / Stripping"),
    ("free estimate", "Free Estimates"),
    ("same day", "Same-Day Service"),
    ("24/7", "24/7 Availability"),
    ("warranty", "Warranty Offered"),
    ("financing", "Financing Available"),
)

_COMPETITOR_DOOR_BRANDS = (
    ("clopay", "Clopay"),
    ("wayne dalton", "Wayne Dalton"),
    ("amarr", "Amarr"),
    ("chi overhead", "CHI Overhead"),
    ("raynor", "Raynor"),
    ("martin door", "Martin Door"),
)

_COMPETITOR_OPENER_BRANDS = (
    ("liftmaster", "LiftMaster"),
    ("chamberlain", "Chamberlain"),
    ("genie", "Genie"),
    ("craftsman", "Craftsman"),
    ("linear", "Linear"),
    ("marantec", "Marantec"),
)


def _extract_serp_keywords(raw_data_json: str) -> list[str]:
    """Pull keyword phrases directly from Firecrawl SERP titles and descriptions."""
    try:
        data = json.loads(raw_data_json) if isinstance(raw_data_json, str) else {}
    except (json.JSONDecodeError, TypeError):
        return []

    items = data.get("data", [])
    if not isinstance(items, list):
        return []

    texts: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        for field in ("title", "description"):
            val = (item.get(field) or "").strip()
            if val:
                texts.append(val)

    combined = re.sub(r"[^a-z0-9\s]", " ", " ".join(texts).lower())
    words = [w for w in combined.split() if w not in _JUNK_WORDS and len(w) > 3]

    bigrams: Counter = Counter()
    trigrams: Counter = Counter()
    for i in range(len(words) - 1):
        bigrams[f"{words[i]} {words[i+1]}"] += 1
    for i in range(len(words) - 2):
        trigrams[f"{words[i]} {words[i+1]} {words[i+2]}"] += 1

    phrases: list[str] = []
    for phrase, count in trigrams.most_common(30):
        if count >= 2:
            phrases.append(phrase)
    for phrase, count in bigrams.most_common(30):
        if count >= 2 and not any(phrase in r for r in phrases):
            phrases.append(phrase)
    return phrases[:20]


def _extract_competitor_intel(research_blob: str) -> dict[str, Any]:
    """Extract structured service, brand, and pricing intel from competitor research text."""
    services = [label for kw, label in _COMPETITOR_SERVICES if kw in research_blob]
    door_brands = [label for kw, label in _COMPETITOR_DOOR_BRANDS if kw in research_blob]
    opener_brands = [label for kw, label in _COMPETITOR_OPENER_BRANDS if kw in research_blob]

    price_hits: list[str] = []
    for match in re.findall(r"\$\d+(?:\.\d{2})?", research_blob):
        if match not in price_hits:
            price_hits.append(match)
    price_anchors = price_hits[:6]

    return {
        "services_competitors_offer": services,
        "door_brands_mentioned": door_brands,
        "opener_brands_mentioned": opener_brands,
        "price_anchors_found": price_anchors,
    }


def build_gap_report(
    *,
    clean_data: dict[str, Any],
    city: str,
    site_url: str | None = None,
    raw_data: str | None = None,
) -> dict[str, Any]:
    """Scrape live site via Firecrawl, compare to research clean_data, return gap report dict."""
    url = (site_url or os.getenv("AUDIT_SITE_URL") or DEFAULT_SITE_URL).strip()
    scrape = _firecrawl_scrape(url)
    data_block = scrape.get("data") if isinstance(scrape.get("data"), dict) else {}
    html = str(data_block.get("html") or "")
    live_meta = _extract_h1_meta(html)
    live_blob = _live_text_blob(scrape)
    research_blob = _research_blob(clean_data)

    # Use SERP titles/descriptions for keywords when raw data is available — much cleaner than Gemma summary
    serp_keywords = _extract_serp_keywords(raw_data or "") if raw_data else []
    keyword_source = serp_keywords if serp_keywords else [p for p, _ in _top_phrases(research_blob, n=20)]

    research_cities = [c for c in _CITY_HINTS if c in research_blob]
    site_cities = [c for c in _CITY_HINTS if c in live_blob]

    # Also check SERP blob for cities and services
    serp_blob = re.sub(r"[^a-z0-9\s]", " ", (raw_data or "").lower())
    combined_blob = research_blob + " " + serp_blob

    services = _service_lexicon()
    missing_services = [s for s in services if s in combined_blob and s not in live_blob]

    cities_missing_on_site = [c for c in research_cities if c not in live_blob]
    if city.strip().lower() and not _mentions_city(live_blob, city):
        if city.strip().lower() not in [x.lower() for x in cities_missing_on_site]:
            cities_missing_on_site.append(city.strip().lower())

    missing_kw = [p for p in keyword_source[:15] if len(p) > 6 and p not in live_blob]

    competitor_intel = _extract_competitor_intel(combined_blob)

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
            "top_research_phrases": keyword_source[:20],
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
        "competitor_intel": competitor_intel,
    }


def write_gap_report(report: dict[str, Any], path: Path | None = None) -> Path:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    out = path or (CLEAN_DIR / "site_gaps.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_csv_paths(name: str) -> list[str] | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or None


def _firecrawl_sdk_client() -> Any:
    from firecrawl import Firecrawl

    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set; cannot run site crawl.")
    base = (os.getenv("FIRECRAWL_BASE_URL") or "https://api.firecrawl.dev").rstrip("/")
    return Firecrawl(api_key=api_key, api_url=base)


def _crawl_job_to_archive_dict(job: Any) -> dict[str, Any]:
    """Serialize crawl job for JSON; truncate very large HTML to keep artifacts usable."""
    if hasattr(job, "model_dump"):
        data = job.model_dump(mode="json")
    else:
        data = {"repr": repr(job)}
    docs = data.get("data")
    if isinstance(docs, list):
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            html = doc.get("html")
            if isinstance(html, str) and len(html) > 120_000:
                doc["html"] = html[:120_000] + "\n<!-- truncated for artifact size -->"
    return data


def crawl_site_firecrawl(
    seed_url: str,
    *,
    limit: int | None = None,
    max_depth: int | None = None,
    include_paths: list[str] | None = None,
    poll_interval: int | None = None,
    timeout_sec: int | None = None,
) -> Any:
    """Run Firecrawl SDK blocking crawl; returns v2 ``CrawlJob``."""
    client = _firecrawl_sdk_client()
    lim = limit if limit is not None else _env_int("AUDITOR_CRAWL_LIMIT", 80)
    depth = max_depth if max_depth is not None else _env_int("AUDITOR_MAX_DEPTH", 3)
    poll = poll_interval if poll_interval is not None else _env_int("AUDITOR_POLL_INTERVAL", 2)
    timeout = timeout_sec if timeout_sec is not None else _env_int("AUDITOR_CRAWL_TIMEOUT", 600)
    paths = include_paths if include_paths is not None else _env_csv_paths("AUDITOR_INCLUDE_PATHS")
    scrape_options: dict[str, Any] = {
        "formats": ["markdown", "html"],
        "only_main_content": False,
    }
    return client.crawl(
        seed_url,
        limit=lim,
        max_discovery_depth=depth,
        include_paths=paths,
        sitemap="include",
        scrape_options=scrape_options,
        poll_interval=poll,
        timeout=timeout,
    )


def save_crawl_raw_artifact(job: Any, *, seed_url: str, params: dict[str, Any]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / f"crawl_dandb_{stamp}.json"
    envelope = {
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed_url": seed_url,
        "crawl_params": {**params, "api_key_note": "redacted; use FIRECRAWL_API_KEY from env"},
        "job": _crawl_job_to_archive_dict(job),
    }
    path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def _row_from_sdk_document(doc: Any) -> dict[str, Any]:
    md = getattr(doc, "markdown", None) or ""
    html = getattr(doc, "html", None) or ""
    url = ""
    title = ""
    meta = getattr(doc, "metadata", None)
    if meta is not None:
        url = (getattr(meta, "url", None) or "") or ""
        title = (getattr(meta, "title", None) or getattr(meta, "og_title", None) or "") or ""
        if not url and hasattr(meta, "model_extra") and meta.model_extra:
            url = str(meta.model_extra.get("source_url") or meta.model_extra.get("sourceURL") or "")
    return {"url": url, "title": str(title).strip(), "markdown": md, "html": html}


def rows_from_crawl_job(job: Any) -> list[dict[str, Any]]:
    data = getattr(job, "data", None) or []
    return [_row_from_sdk_document(d) for d in data]


def _url_has_boca_location(url: str) -> bool:
    u = url.rstrip("/").lower()
    return BOCA_PAGE_FRAGMENT.lower() in u


def pick_boca_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        if _url_has_boca_location(row.get("url") or ""):
            return row
    return None


def _useless_research_markdown(md: str) -> bool:
    m = md.strip().lower()
    if len(m) < 40:
        return True
    if "please enable js" in m:
        return True
    if m.startswith("skip to content") and len(m) < 200:
        return False
    return False


def load_research_blueprint(research_path: Path) -> dict[str, Any]:
    """Load Firecrawl search export and extract competitor markdown for Boca gap checks."""
    blob = json.loads(research_path.read_text(encoding="utf-8"))
    web_raw = []
    if isinstance(blob.get("data"), dict):
        web_raw = blob["data"].get("web") or []
    entries: list[dict[str, Any]] = []
    for item in web_raw:
        if not isinstance(item, dict):
            continue
        md = str(item.get("markdown") or "")
        meta = item.get("metadata")
        if _useless_research_markdown(md):
            continue
        if isinstance(meta, dict):
            sc = meta.get("statusCode") or meta.get("status_code")
            try:
                if sc is not None and int(sc) >= 400:
                    continue
            except (TypeError, ValueError):
                pass
        entries.append(
            {
                "url": str(item.get("url") or ""),
                "title": str(item.get("title") or ""),
                "description": str(item.get("description") or ""),
                "markdown": md,
            }
        )

    priority: list[dict[str, Any]] = []
    for e in entries:
        u = e["url"].lower()
        title_desc = (e["title"] + " " + e["description"]).lower()
        if "broten.com" in u and "boca" in u:
            priority.append(e)
        elif "palmbeachdoors.com" in u:
            priority.append(e)
        elif "flgaragedoor.com" in u and ("boca" in u or "precision" in title_desc):
            priority.append(e)
        elif "mrfixitdoors.com" in u and "boca" in u:
            priority.append(e)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for e in priority:
        key = e["url"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    blueprint_text = "\n\n".join(p["markdown"] for p in deduped).lower()
    return {
        "entries": entries,
        "priority_competitors": deduped,
        "blueprint_text": blueprint_text,
        "blueprint_word_count": len(re.split(r"\s+", blueprint_text)) if blueprint_text else 0,
    }


def _extra_landmarks_from_blueprint(blueprint: str, *, min_len: int = 10) -> list[str]:
    """Heuristic: multi-token phrases in blueprint that look like local place names."""
    candidates = []
    for m in re.finditer(r"\b([a-z]+(?:\s+[a-z]+){1,3})\b", blueprint):
        phrase = m.group(1).strip()
        if len(phrase) < min_len:
            continue
        if not any(
            k in phrase
            for k in ("boca", "beach", "park", "cove", "raton", "palm", "delray", "deerfield", "mar", "florida")
        ):
            continue
        if phrase not in candidates:
            candidates.append(phrase)
    freq = Counter()
    for c in candidates:
        freq[c] = blueprint.count(c)
    return [p for p, n in freq.most_common(12) if n >= 2]


def _word_count(text: str) -> int:
    if not text or not text.strip():
        return 0
    return len(re.findall(r"\w+", text))


def _collect_jsonld_types(html: str) -> tuple[set[str], list[str]]:
    notes: list[str] = []
    if not html:
        return set(), notes
    types_set: set[str] = set()
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    ):
        raw = block.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            notes.append("Unparseable JSON-LD block skipped.")
            continue
        stack = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                t = cur.get("@type")
                if isinstance(t, str):
                    types_set.add(t)
                elif isinstance(t, list):
                    for x in t:
                        if isinstance(x, str):
                            types_set.add(x)
                for v in cur.values():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(cur, list):
                stack.extend(cur)
    return types_set, notes


def _live_blob(row: dict[str, Any]) -> str:
    return f"{row.get('markdown') or ''}\n{row.get('html') or ''}".lower()


def _pattern_hits(blob: str, patterns: tuple[tuple[str, str], ...]) -> dict[str, bool]:
    return {label: (pat in blob) for pat, label in patterns}


def build_site_gap_analysis_markdown(
    *,
    seed_url: str,
    crawl_job: Any,
    crawl_rows: list[dict[str, Any]],
    raw_artifact: Path,
    boca_row: dict[str, Any],
    blueprint: dict[str, Any],
    crawl_params: dict[str, Any],
) -> str:
    live_blob = _live_blob(boca_row)
    bp = blueprint["blueprint_text"]
    extra_landmarks = _extra_landmarks_from_blueprint(bp)

    landmark_table = []
    all_landmarks = list(dict.fromkeys(list(_BOCA_LOCAL_ENTITIES) + extra_landmarks))[:35]
    for lm in all_landmarks:
        on_live = "Yes" if lm in live_blob else "No"
        in_bp = "Yes" if lm in bp else "No"
        landmark_table.append(f"| {lm} | {in_bp} | {on_live} |")

    conv_live = _pattern_hits(live_blob, _CONVERSION_PATTERNS)
    conv_bp = _pattern_hits(bp, _CONVERSION_PATTERNS)
    conv_lines = [
        f"| {label} | {'Yes' if conv_bp.get(label) else 'No'} | {'Yes' if conv_live.get(label) else 'No'} |"
        for label in conv_bp
    ]

    brand_lines = []
    for token, label in _BRAND_ENTITY_CHECKS:
        brand_lines.append(
            f"| {label} | {'Yes' if token.replace('-', ' ') in bp or token in bp else 'No'} | "
            f"{'Yes' if token.replace('-', ' ') in live_blob or token in live_blob else 'No'} |"
        )

    tech_bp = any(s in bp for s in _TECH_BIO_SIGNALS)
    tech_live = any(s in live_blob for s in _TECH_BIO_SIGNALS)

    live_wc = _word_count(boca_row.get("markdown") or "")
    bench_rows = []
    for p in blueprint["priority_competitors"]:
        wc = _word_count(p.get("markdown") or "")
        bench_rows.append(f"| {p.get('url', '')} | {wc} |")
    bench_md = "\n".join(bench_rows) if bench_rows else "| (none) | — |"

    median_hint = ""
    wcs = [_word_count(p.get("markdown") or "") for p in blueprint["priority_competitors"]]
    if wcs:
        med = sorted(wcs)[len(wcs) // 2]
        median_hint = f"Median competitor markdown word count (priority URLs): **{med}**. Live Boca page: **{live_wc}**."
        if live_wc < 500:
            median_hint += " Live page is under **500 words** (thin vs many local winners)."
        if med > 0 and live_wc < med * 0.5:
            median_hint += " Live copy is well under half the median competitor length."

    schema_types, schema_notes = _collect_jsonld_types(boca_row.get("html") or "")
    has_faq = "FAQPage" in schema_types
    has_review = "Review" in schema_types or "AggregateRating" in schema_types
    schema_lines = [
        f"- Detected JSON-LD `@type` values: {', '.join(sorted(schema_types)) or '*(none)*'}",
        f"- FAQPage present: **{'Yes' if has_faq else 'No'}**",
        f"- Review / AggregateRating present: **{'Yes' if has_review else 'No'}**",
        "- Competitor pattern note: top Boca SERP pages (e.g. Broten, franchise Precision) often pair long-form copy with reviews/testimonials; match FAQ/Review schema where truthful.",
    ]
    schema_lines.extend(f"- {n}" for n in schema_notes[:3])

    phone_header = bool(re.search(r"tel:\s*\+?\d", (boca_row.get("markdown") or "")[:2500], re.I))

    lines: list[str] = [
        "# Site-wide gap analysis (Priority One Auditor)",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"- **Seed URL:** {seed_url}",
        f"- **Boca page audited:** {boca_row.get('url')}",
        f"- **Raw crawl artifact:** `{raw_artifact.relative_to(ROOT_DIR)}`",
        f"- **Crawl status:** {getattr(crawl_job, 'status', '?')} — pages: **{len(crawl_rows)}** — credits used: **{getattr(crawl_job, 'credits_used', '?')}**",
        f"- **Crawl limits used:** `{json.dumps(crawl_params, ensure_ascii=False)}`",
        "",
        "Also see JSON homepage audit from LangGraph: `data/clean/site_gaps.json` (single-page scrape).",
        "",
        "## Executive summary",
        "",
        "This report compares your live **Boca Raton location** page against competitor markdown from `.firecrawl/research-boca-raton.json`, "
        "plus a recursive Firecrawl crawl of your site for URL/title inventory and the Boca page HTML (schema).",
        "",
        median_hint or "*(Add competitor markdown to research file for word-count benchmarks.)*",
        "",
        "## Site inventory (crawl)",
        "",
        "| URL | Title |",
        "| --- | --- |",
    ]
    for row in sorted(crawl_rows, key=lambda r: (r.get("url") or "")):
        u = (row.get("url") or "").replace("|", "\\|")
        t = (row.get("title") or "").replace("|", "\\|")[:120]
        lines.append(f"| {u} | {t} |")

    lines.extend(
        [
            "",
            "## Landmark and neighborhood coverage",
            "",
            "| Entity / phrase | In competitor blueprint | On live Boca page |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(landmark_table)

    lines.extend(
        [
            "",
            "## Conversion and trust hooks",
            "",
            "| Signal | In blueprint | On live Boca page |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(conv_lines)
    lines.append(f"| Phone visible early in page markdown (first ~2.5k chars) | — | {'Yes' if phone_header else 'No'} |")

    lines.extend(
        [
            "",
            "## Brand, offers, and depth signals",
            "",
            "| Check | In blueprint | On live Boca page |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(brand_lines)
    lines.append(f"| Technician / team bios (heuristic) | {'Yes' if tech_bp else 'No'} | {'Yes' if tech_live else 'No'} |")

    lines.extend(
        [
            "",
            "## Content depth (word counts)",
            "",
            "| Source | Markdown word count |",
            "| --- | ---: |",
            f"| Live Boca page | {live_wc} |",
            bench_md,
            "",
            "## Schema (live Boca page)",
            "",
        ]
    )
    lines.extend(schema_lines)

    lines.extend(
        [
            "",
            "## Prioritized recommendations",
            "",
            "1. Close **landmark gaps** where competitors mention neighborhoods you omit (only where accurate for your service area).",
            "2. Add truthful **FAQPage** / **Review** structured data if you publish FAQs and real reviews.",
            "3. Expand Boca page body copy toward competitor depth if it is thin (<500 words) while staying factual.",
            "4. Surface **24/7 or emergency** positioning and tune-up offers only if operationally true; mirror competitor *patterns*, not unverifiable claims.",
            "",
            "## Appendix: competitor URLs used as blueprint",
            "",
        ]
    )
    for p in blueprint["priority_competitors"]:
        lines.append(f"- {p.get('url')}")
        snippet = (p.get("markdown") or "")[:1200].replace("\r", "")
        lines.extend(["", "```markdown", snippet, "```", ""])

    return "\n".join(lines) + "\n"


def append_priority_one_workflow_log() -> None:
    WORKFLOW_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = f"- [{ts}] - Site-wide audit completed. Gap analysis for Boca Raton generated.\n"
    with WORKFLOW_STATE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


def run_priority_one_site_audit(
    *,
    seed_url: str | None = None,
    research_path: Path | None = None,
) -> Path:
    """CLI: crawl site, compare Boca page vs research blueprint, write Markdown + workflow log."""
    seed = (seed_url or os.getenv("AUDIT_SITE_URL") or DEFAULT_SITE_URL).strip()
    research = research_path or Path(
        os.getenv("AUDITOR_RESEARCH_JSON", str(DEFAULT_RESEARCH_JSON))
    ).resolve()

    params = {
        "limit": _env_int("AUDITOR_CRAWL_LIMIT", 80),
        "max_discovery_depth": _env_int("AUDITOR_MAX_DEPTH", 3),
        "include_paths": _env_csv_paths("AUDITOR_INCLUDE_PATHS"),
        "sitemap": "include",
        "poll_interval": _env_int("AUDITOR_POLL_INTERVAL", 2),
        "timeout": _env_int("AUDITOR_CRAWL_TIMEOUT", 600),
    }

    job = crawl_site_firecrawl(
        seed,
        limit=params["limit"],
        max_depth=params["max_discovery_depth"],
        include_paths=params["include_paths"],
        poll_interval=params["poll_interval"],
        timeout_sec=params["timeout"],
    )
    status = getattr(job, "status", "")
    if status != "completed":
        raise RuntimeError(f"Firecrawl crawl did not complete (status={status!r}).")

    raw_path = save_crawl_raw_artifact(job, seed_url=seed, params=params)
    rows = rows_from_crawl_job(job)
    boca = pick_boca_row(rows)
    if boca is None:
        scrape = _firecrawl_scrape(urljoin(seed.rstrip("/") + "/", "locations/boca-raton/"))
        data_block = scrape.get("data") if isinstance(scrape.get("data"), dict) else {}
        boca = {
            "url": urljoin(seed.rstrip("/") + "/", "locations/boca-raton/"),
            "title": "",
            "markdown": str(data_block.get("markdown") or ""),
            "html": str(data_block.get("html") or ""),
        }

    blueprint = load_research_blueprint(research)
    md = build_site_gap_analysis_markdown(
        seed_url=seed,
        crawl_job=job,
        crawl_rows=rows,
        raw_artifact=raw_path,
        boca_row=boca,
        blueprint=blueprint,
        crawl_params=params,
    )

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    GAP_MARKDOWN_PATH.write_text(md, encoding="utf-8")
    append_priority_one_workflow_log()
    return GAP_MARKDOWN_PATH


def run_audit_and_save(
    clean_data: dict[str, Any],
    *,
    city: str,
    site_url: str | None = None,
    raw_data: str | None = None,
) -> Path:
    """Build gap report and write ``/data/clean/site_gaps.json``."""
    report = build_gap_report(clean_data=clean_data, city=city, site_url=site_url, raw_data=raw_data)
    return write_gap_report(report)


if __name__ == "__main__":
    try:
        out = run_priority_one_site_audit()
        print(f"Wrote {out.relative_to(ROOT_DIR)}", file=sys.stderr)
    except Exception as exc:
        print(f"Auditor failed: {exc}", file=sys.stderr)
        sys.exit(1)
