"""Human-in-the-loop notifications (Discord webhook and/or Resend email)."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=False)

from agents.discord_bridge import agent_content, agent_footer, discord_webhook_url, hitl_channel_id, post_discord_payload


def _truncate(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n - 3] + "..."


def _extract_h1(html: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return ""


def _count_words(html: str) -> int:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(text.split())


def _extract_headings(html: str) -> list[str]:
    matches = re.findall(r"<h[2-3][^>]*>(.*?)</h[2-3]>", html, re.I | re.S)
    return [re.sub(r"<[^>]+>", "", m).strip() for m in matches if m.strip()]


def _plain_text(html: str) -> str:
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", "", t)
    return re.sub(r"<[^>]+>", " ", t).lower()


def _build_diff_embed(city: str, new_html: str, old_html: str) -> dict[str, Any] | None:
    """Compare new page to previous version and return a Discord embed showing what changed."""
    old_text = _plain_text(old_html)
    new_text = _plain_text(new_html)
    old_wc = len(old_text.split())
    new_wc = len(new_text.split())
    wc_delta = new_wc - old_wc

    old_headings = set(_extract_headings(old_html))
    new_headings = set(_extract_headings(new_html))
    added_headings = [h for h in new_headings if h not in old_headings]
    removed_headings = [h for h in old_headings if h not in new_headings]

    # Neighborhood / local signal diff
    _LOCAL_SIGNALS = [
        "mizner park", "royal palm yacht", "town center", "spanish river", "boca west",
        "broken sound", "camino real", "royal palm place", "sandalfoot", "east boca",
        "west boca", "intracoastal", "jupiter inlet", "abacoa", "palm beach lakes",
        "cityplace", "clematis", "northwood", "palm beach polo", "ibis golf",
        "wellington green", "boynton town", "delray market", "atlantic avenue",
        "mizner boulevard", "glades road", "military trail",
    ]
    added_local = [s for s in _LOCAL_SIGNALS if s in new_text and s not in old_text]

    # Service / keyword diff
    _SERVICE_SIGNALS = [
        "clopay", "liftmaster", "hurricane", "impact rated", "smart garage", "wifi",
        "financing", "warranty", "free estimate", "same day", "24/7", "emergency",
        "commercial", "spring replacement", "cable repair", "panel replacement",
        "tune-up", "carriage house", "insulated",
    ]
    added_services = [s for s in _SERVICE_SIGNALS if s in new_text and s not in old_text]

    fields: list[dict[str, Any]] = [
        {
            "name": "📊 Word Count",
            "value": f"{old_wc:,} → {new_wc:,} ({'+' if wc_delta >= 0 else ''}{wc_delta:,} words)",
            "inline": True,
        }
    ]
    if added_headings:
        fields.append({
            "name": "➕ New Sections Added",
            "value": _bullet_list(added_headings, 8),
            "inline": False,
        })
    if removed_headings:
        fields.append({
            "name": "➖ Sections Removed",
            "value": _bullet_list(removed_headings, 5),
            "inline": False,
        })
    if added_local:
        fields.append({
            "name": "📍 New Neighborhoods/Landmarks",
            "value": _bullet_list([s.title() for s in added_local], 8),
            "inline": True,
        })
    if added_services:
        fields.append({
            "name": "🔧 New Services/Keywords",
            "value": _bullet_list([s.title() for s in added_services], 8),
            "inline": True,
        })
    if len(fields) == 1 and wc_delta == 0:
        return None  # Nothing meaningful changed

    return {
        "title": f"📝 What Changed — {city}",
        "color": 0x9B59B6,
        "fields": fields,
    }


def _bullet_list(items: list[str], limit: int = 10, empty: str = "None detected") -> str:
    if not items:
        return empty
    return "\n".join(f"• {item}" for item in items[:limit])


def _build_discord_embeds(
    city: str,
    content_draft: str,
    thread_id: str,
    gap_report: dict[str, Any],
) -> list[dict[str, Any]]:
    is_hub = city.strip().lower().startswith("hub:")
    h1 = _extract_h1(content_draft) or f"{city} Garage Door Repair | D&B"
    word_count = _count_words(content_draft)

    gaps = gap_report.get("gaps", {})
    research = gap_report.get("research_context", {})
    intel = gap_report.get("competitor_intel", {})

    missing_kw = gaps.get("missing_keywords_vs_live_site", [])
    missing_services = gaps.get("services_missing_from_live_homepage_copy", [])
    missing_cities = gaps.get("cities_in_research_not_emphasized_on_homepage", [])

    comp_services = intel.get("services_competitors_offer", [])
    door_brands = intel.get("door_brands_mentioned", [])
    opener_brands = intel.get("opener_brands_mentioned", [])
    price_anchors = intel.get("price_anchors_found", [])
    top_phrases = research.get("top_research_phrases", [])

    if is_hub:
        approve_instructions = (
            "Use the **✅ Approve** / **❌ Reject** buttons on the follow-up message in this channel. "
            "Topical hub: `resume_hitl.py` does not apply — keep `writer_node --hitl` running here, "
            "or use a separate Discord bot process (it reads `data/hub_hitl_pending/`)."
        )
        reject_instructions = "Use **❌ Reject** on the button message (or wait for CLI timeout)."
    else:
        approve_instructions = f"```\npython resume_hitl.py \"{thread_id}\" approve\n```"
        reject_instructions = f"```\npython resume_hitl.py \"{thread_id}\" reject\n```"

    # Embed 1: page summary + approve/reject
    embed_page: dict[str, Any] = {
        "title": f"{'📚 Hub Page Ready' if is_hub else '📄 SEO Page Ready'} — {city}",
        "color": 0x1ABC9C if is_hub else 0x2ECC71,
        "fields": [
            {"name": "H1 Title", "value": _truncate(h1, 256), "inline": False},
            {"name": "Word Count", "value": f"~{word_count:,} words", "inline": True},
            {"name": "Thread ID", "value": f"`{thread_id}`", "inline": True},
            {
                "name": "Approve",
                "value": _truncate(approve_instructions, 1024),
                "inline": False,
            },
            {
                "name": "Reject",
                "value": _truncate(reject_instructions, 1024),
                "inline": False,
            },
        ],
    }

    # Embed 2: competitor services & brands
    comp_fields: list[dict[str, Any]] = []

    if comp_services:
        comp_fields.append({
            "name": "🔧 Services Competitors Advertise",
            "value": _bullet_list(comp_services, 15),
            "inline": False,
        })

    brands_combined = door_brands + opener_brands
    if brands_combined:
        comp_fields.append({
            "name": "🏷️ Brands Mentioned by Competitors",
            "value": _bullet_list(brands_combined, 12),
            "inline": True,
        })

    if price_anchors:
        comp_fields.append({
            "name": "💰 Price Anchors Found",
            "value": _bullet_list(price_anchors, 6),
            "inline": True,
        })

    if top_phrases:
        comp_fields.append({
            "name": "🔑 Top Competitor Keywords",
            "value": _bullet_list(top_phrases[:12], 12),
            "inline": False,
        })

    embed_intel: dict[str, Any] = {
        "title": "🏆 Competitor Intelligence",
        "color": 0xF39C12,
        "fields": comp_fields or [{"name": "Status", "value": "No competitor data extracted", "inline": False}],
    }

    # Embed 3: content gaps closed in this page
    gap_fields: list[dict[str, Any]] = []

    if missing_kw:
        gap_fields.append({
            "name": "📈 Keywords Added (not on homepage)",
            "value": _bullet_list(missing_kw, 10),
            "inline": False,
        })
    if missing_services:
        gap_fields.append({
            "name": "✅ Services Gaps Closed",
            "value": _bullet_list(missing_services, 10),
            "inline": True,
        })
    if missing_cities:
        gap_fields.append({
            "name": "📍 Cities Reinforced",
            "value": _bullet_list(missing_cities, 8),
            "inline": True,
        })

    embed_gaps: dict[str, Any] = {
        "title": "🔍 Gaps Closed in This Page",
        "color": 0x3498DB,
        "fields": gap_fields or [{"name": "Status", "value": "No gaps detected vs homepage", "inline": False}],
        "footer": {"text": agent_footer("SEO Factory", "D&B Garage Doors")},
    }

    return [embed_page, embed_intel, embed_gaps]


def _find_previous_html(city: str) -> str | None:
    """Find the previously generated HTML for this city, if any."""
    slug = re.sub(r"[^\w\-]+", "_", city.strip().lower()).strip("_")
    clean_dir = ROOT / "data" / "clean"
    files = sorted(clean_dir.glob(f"{slug}_pipeline_*.html"), key=lambda p: p.stat().st_mtime)
    if len(files) >= 2:
        return files[-2].read_text(encoding="utf-8")
    return None


def notify_hub_draft(*, topic: str, output_path: Path, html: str) -> bool:
    """Post a topical hub draft summary to Discord (same ``DISCORD_WEBHOOK_URL`` as HITL / pipeline)."""
    webhook = discord_webhook_url()
    if not webhook:
        return False

    h1 = _extract_h1(html) or topic
    word_count = _count_words(html)
    rel = output_path
    try:
        rel = output_path.relative_to(ROOT)
    except ValueError:
        pass
    preview = _truncate(re.sub(r"<[^>]+>", " ", html).strip(), 400)

    payload: dict[str, Any] = {
        "username": "D&B SEO Hub Writer",
        "content": agent_content(f"Topical authority hub generated — `{topic}`"),
        "embeds": [
            {
                "title": "📚 Hub page draft",
                "color": 0x1ABC9C,
                "fields": [
                    {"name": "Topic slug", "value": _truncate(topic, 256), "inline": True},
                    {"name": "H1", "value": _truncate(h1, 256), "inline": True},
                    {"name": "Word count (approx)", "value": f"~{word_count:,}", "inline": True},
                    {"name": "Saved to", "value": f"`{rel}`", "inline": False},
                    {"name": "Text preview", "value": preview or "(empty)", "inline": False},
                ],
                "footer": {"text": agent_footer("SEO Factory", "D&B Garage Doors", "Hub Writer")},
            }
        ],
    }
    return post_discord_payload(payload, webhook_url=webhook)


def notify_human_review(
    *,
    city: str,
    content_draft: str,
    thread_id: str,
    gap_report: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Notify operator with clean competitor intel and approval instructions."""
    gap = gap_report or {}
    is_hub = city.strip().lower().startswith("hub:")

    webhook = discord_webhook_url()
    if webhook:
        embeds = _build_discord_embeds(city, content_draft, thread_id, gap)

        # Add diff embed if a previous version exists
        previous_html = None if is_hub else _find_previous_html(city)
        if previous_html:
            diff_embed = _build_diff_embed(city, content_draft, previous_html)
            if diff_embed:
                embeds.append(diff_embed)

        headline = (
            agent_content(f"Hub draft ready for review — {city} | Thread `{thread_id}`")
            if is_hub
            else agent_content(f"New SEO Page Ready — {city} | Thread `{thread_id}`")
        )
        payload: dict[str, Any] = {
            "username": "D&B SEO Orchestrator",
            "content": headline,
            "embeds": embeds,
        }
        post_discord_payload(payload, webhook_url=webhook)

    # If the bot is running (DISCORD_BOT_TOKEN + DISCORD_HITL_CHANNEL_ID set),
    # queue a button message so the user can click ✅/❌ instead of typing commands.
    if os.getenv("DISCORD_BOT_TOKEN", "").strip() and hitl_channel_id() is not None:
        from agents import hitl_gate
        hitl_gate.queue_button_message(city, thread_id)

    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    from_addr = os.getenv("RESEND_FROM_EMAIL", "").strip()
    to_addr = os.getenv("HITL_NOTIFY_EMAIL", "").strip()
    if resend_key and from_addr and to_addr:
        gaps = gap.get("gaps", {})
        intel = gap.get("competitor_intel", {})
        lines = [
            f"<h2>SEO Page Ready — {city}</h2>",
            f"<p><b>Thread ID:</b> <code>{thread_id}</code></p>",
            "<h3>Approve / Reject</h3>",
            f"<pre>python resume_hitl.py \"{thread_id}\" approve</pre>",
            f"<pre>python resume_hitl.py \"{thread_id}\" reject</pre>",
            "<h3>Competitor Services</h3>",
            "<ul>" + "".join(f"<li>{s}</li>" for s in intel.get("services_competitors_offer", [])) + "</ul>",
            "<h3>Brands Competitors Mention</h3>",
            "<ul>" + "".join(
                f"<li>{b}</li>" for b in intel.get("door_brands_mentioned", []) + intel.get("opener_brands_mentioned", [])
            ) + "</ul>",
            "<h3>Missing Keywords vs Homepage</h3>",
            "<ul>" + "".join(f"<li>{k}</li>" for k in gaps.get("missing_keywords_vs_live_site", [])) + "</ul>",
        ]
        if extra:
            lines.append(f"<h3>Extra Context</h3><pre>{_html_escape(str(extra)[:1000])}</pre>")
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
            json={
                "from": from_addr,
                "to": [to_addr],
                "subject": f"[{agent_footer('SEO Factory')}] Review publish — {city}",
                "html": "\n".join(lines),
            },
            timeout=30.0,
        )


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
