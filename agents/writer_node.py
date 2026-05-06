"""Standalone writer node for city and topical authority hub pages."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.discord_hitl_bot import start_bot_in_thread
from agents.hitl_gate import pop_result, queue_button_message, register
from agents.hub_hitl import clear_hub_pending, consume_resolved, publish_hub_to_worker, save_hub_pending
from agents.notifier import notify_hub_draft, notify_human_review

load_dotenv(_REPO_ROOT / ".env", override=False)

# Eight Palm Beach County service cities (spokes). Paths: /locations/[city]/
SERVICE_CITIES: tuple[tuple[str, str], ...] = (
    ("Boca Raton", "boca-raton"),
    ("West Palm Beach", "west-palm-beach"),
    ("Delray Beach", "delray-beach"),
    ("Boynton Beach", "boynton-beach"),
    ("Wellington", "wellington"),
    ("Jupiter", "jupiter"),
    ("Palm Beach Gardens", "palm-beach-gardens"),
    ("Lake Worth", "lake-worth"),
)

HUB_PROMPT_INSTRUCTION = """
You are now writing a 'Topical Authority Hub' page for D&B Garage Doors.
- Tone: Expert, authoritative, and helpful.
- Local Signal: Mention specific Palm Beach County building codes and climate issues.
- Requirement: Must include License #CGC1519508 and Phone 561-305-5853.
- Linking: Leave placeholders like [INTERNAL_LINK_CITY_PAGES] where the bot should insert links to the 8 city pages.
"""


def _project_root() -> Path:
    return _REPO_ROOT


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def city_pages_internal_links_html() -> str:
    """HTML block linking every hub to all eight city location pages (topical hub → spoke)."""
    base = (os.getenv("CITY_PAGE_BASE_PATH") or "/locations").rstrip("/") + "/"
    lis = "".join(
        f'<li><a href="{base}{slug}/">{label}</a></li>' for label, slug in SERVICE_CITIES
    )
    return f'<nav aria-label="Garage door service by city"><ul>{lis}</ul></nav>'


def _inject_city_page_links(html: str) -> str:
    return html.replace("[INTERNAL_LINK_CITY_PAGES]", city_pages_internal_links_html())


def _append_workflow_log(summary: str) -> None:
    log_path = _project_root() / "docs" / "workflow_state.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"- [{ts}] - Hub Writer: {summary}\n")


def _brand_header_line() -> str:
    return "D&B Garage Doors | License #CGC1519508 | Phone 561-305-5853"


def _hub_wrapper(title: str, h1: str, main_inner: str) -> str:
    brand = _brand_header_line()
    return (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title></head><body>"
        f"<header><h1>{h1}</h1><p>{brand}</p></header><main>{main_inner}"
        f"<section><h2>Garage door service in your city</h2><p>[INTERNAL_LINK_CITY_PAGES]</p></section>"
        f"<section><h2>Talk to a local expert</h2>"
        f"<p>Call 561-305-5853 — D&B Garage Doors (License #CGC1519508).</p></section>"
        f"</main><footer><p>{brand}</p></footer></body></html>"
    )


def _hub_draft_html(topic: str) -> str:
    """Deterministic hub HTML by topic slug (Phase 1 factory output). Extend per master guide."""
    t = _slugify(topic)

    if "hurricane" in t or "impact-rating" in t or "hvhz" in t:
        inner = (
            "<section><h2>Why impact ratings matter in Palm Beach County</h2>"
            "<p>Palm Beach County homes face hurricane-force wind loads, debris risk, and code compliance "
            "requirements that make proper garage door ratings essential.</p></section>"
            "<section><h2>Key Florida entities and standards</h2><ul>"
            "<li>Miami-Dade NOA</li><li>ASCE 7-16 wind-load standards</li><li>180 mph wind considerations</li>"
            "</ul></section>"
            "<section><h2>HVHZ and local compliance checklist</h2>"
            "<p>Verify design pressure labels, reinforcement hardware, and permit documentation before "
            "installation.</p></section>"
            "<section><h2>Salt air and summer heat</h2>"
            "<p>Coastal salt and humidity accelerate hardware wear; pair rated assemblies with corrosion-resistant "
            "components and seasonal maintenance.</p></section>"
        )
        return _hub_wrapper(
            "Hurricane impact ratings in Florida: homeowner guide",
            "Hurricane impact ratings 101 for South Florida garage doors",
            inner,
        )

    if "salt" in t or "corrosion" in t or "coastal" in t:
        inner = (
            "<section><h2>Salt-air corrosion and coastal garage doors</h2>"
            "<p>Homes near the Atlantic in Boca Raton, Jupiter, and along A1A see salt mist and humidity that "
            "speed rust on springs, hinges, and fasteners. Planning for corrosion resistance is as important as "
            "storm ratings.</p></section>"
            "<section><h2>What to prioritize</h2><ul>"
            "<li>Rust-resistant or coated torsion/extension springs</li>"
            "<li>Nylon rollers vs. uncoated steel on exposed tracks</li>"
            "<li>Scheduled lubrication with products suited to Florida humidity</li>"
            "<li>Hardware and fasteners rated for coastal exposure where available</li>"
            "</ul></section>"
            "<section><h2>Maintenance rhythm for Palm Beach County</h2>"
            "<p>Inspect quarterly for surface rust, listen for grinding rollers, and clear track debris after "
            "storms. Address minor oxidation before it seizes hardware.</p></section>"
        )
        return _hub_wrapper(
            "Salt-air garage door corrosion prevention | South Florida",
            "Salt-air corrosion prevention for coastal Florida garage doors",
            inner,
        )

    if "heat" in t or "insulation" in t or "summer" in t or "r-value" in t:
        inner = (
            "<section><h2>Garage doors in 90°+ South Florida heat</h2>"
            "<p>Uninsulated garages act like ovens; heat stresses openers, batteries, and lubricants while "
            "increasing cooling load on adjacent living space.</p></section>"
            "<section><h2>Insulation and materials</h2><ul>"
            "<li>R-value and polyurethane vs. polystyrene panels</li>"
            "<li>Ventilation and weather seal integrity</li>"
            "<li>Battery backup openers for outage periods after summer storms</li>"
            "</ul></section>"
        )
        return _hub_wrapper(
            "Garage door insulation and summer heat in Florida",
            "The summer heat guide: insulation and opener longevity in Florida",
            inner,
        )

    if "safety" in t or "security" in t or "myq" in t or "fishing" in t:
        inner = (
            "<section><h2>Garage door safety and break-in resistance</h2>"
            "<p>Protect against fishing attacks on emergency releases, keep remotes out of sight, and use "
            "rolling-code or modern encrypted systems where possible.</p></section>"
            "<section><h2>Smart access</h2>"
            "<p>LiftMaster MyQ and similar platforms add monitoring and vacation-style lockout habits; pair "
            "technology with physical security (side locks, reinforced strike, lighting).</p></section>"
        )
        return _hub_wrapper(
            "Garage door safety and security in Florida",
            "Garage door safety and smart security for Florida homeowners",
            inner,
        )

    if "spring" in t or "emergency" in t:
        inner = (
            "<section><h2>Why springs fail faster in Florida humidity</h2>"
            "<p>Moisture and temperature cycles accelerate metal fatigue. High-cycle springs and correct "
            "balance reduce wear on openers and cables.</p></section>"
            "<section><h2>Torsion vs. extension</h2>"
            "<p>Know which system you have, never adjust high-tension hardware without training, and replace "
            "pairs when recommended to maintain door balance.</p></section>"
        )
        return _hub_wrapper(
            "Emergency spring repair and Florida humidity",
            "Emergency spring repair: Florida humidity and garage door springs",
            inner,
        )

    inner = (
        "<section><h2>Florida topical guide</h2>"
        f"<p>Topic: {_slugify(topic)}. This placeholder hub should be expanded with research-backed sections.</p>"
        "</section>"
    )
    return _hub_wrapper(
        f"D&B Garage Doors | {_slugify(topic)}",
        "South Florida garage door guide",
        inner,
    )


def generate_hub(topic: str, *, notify_discord: bool = False) -> Path:
    html = _hub_draft_html(topic)
    html = _inject_city_page_links(html)

    out_dir = _project_root() / "data" / "hub_pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"hub_{_slugify(topic)}_{stamp}.html"
    out_path = out_dir / filename
    out_path.write_text(html, encoding="utf-8")

    _append_workflow_log(f"generated={filename}; topic={topic!r}; chars={len(html)}")
    if notify_discord:
        sent = notify_hub_draft(topic=topic, output_path=out_path, html=html)
        if sent:
            print("Discord: hub notification sent.")
        else:
            print(
                "Discord: skipped or failed (set DISCORD_WEBHOOK_URL in .env, same as SEO pipeline).",
                flush=True,
            )
    return out_path


def run_hub_with_hitl(topic: str) -> int:
    """Generate hub HTML, notify Discord like the city pipeline, wait for approve/deny, then publish if approved."""
    start_bot_in_thread()
    if not os.getenv("DISCORD_BOT_TOKEN", "").strip():
        print(
            "[HITL] No DISCORD_BOT_TOKEN — in-process button queue may be empty. "
            "Run `python agents/discord_hitl_bot.py` in another terminal, or set the token so this process can post buttons.",
            flush=True,
        )

    thread_id = str(uuid.uuid4())
    out_path = generate_hub(topic, notify_discord=False)
    html = out_path.read_text(encoding="utf-8")
    hub_slug = _slugify(topic)

    save_hub_pending(thread_id, topic=topic, hub_slug=hub_slug, html_path=out_path)

    event = register(thread_id)
    notify_human_review(
        city=f"Hub: {topic}",
        content_draft=html,
        thread_id=thread_id,
        gap_report={},
    )
    queue_button_message(f"Hub: {topic}", thread_id)

    timeout = int(os.getenv("HITL_TIMEOUT_SECONDS", "3600"))
    deadline = time.time() + timeout
    approved = False
    external_publish: dict | None = None

    print(f"[HITL] thread_id={thread_id}")
    print(f"[HITL] Waiting for Discord approval (timeout {timeout}s)…")
    print(
        f"[HITL] If the CLI is stuck after you clicked a button, run:\n"
        f"     python resume_hub_hitl.py {thread_id} reject",
        flush=True,
    )

    while time.time() < deadline:
        resolved = consume_resolved(thread_id)
        if resolved is not None:
            approved = bool(resolved.get("approved"))
            external_publish = resolved.get("publish_result") if isinstance(resolved.get("publish_result"), dict) else None
            break
        if event.wait(1.0):
            approved = pop_result(thread_id)
            external_publish = None
            break
    else:
        print("[HITL] Timed out — no publish. Pending hub state cleared.")
        clear_hub_pending(thread_id)
        _append_workflow_log(f"hub_hitl_timeout; topic={topic!r}; thread_id={thread_id}")
        return 1

    clear_hub_pending(thread_id)

    if approved:
        if external_publish is None:
            publish_result = publish_hub_to_worker(html, hub_slug=hub_slug, topic=topic)
        else:
            publish_result = external_publish
        print("publish_result:", publish_result)
        _append_workflow_log(
            f"hub_hitl_published; topic={topic!r}; thread_id={thread_id}; deploy={publish_result.get('deploy', publish_result)}"
        )
        return 0

    print("[HITL] Rejected — hub not published.")
    _append_workflow_log(f"hub_hitl_rejected; topic={topic!r}; thread_id={thread_id}")
    return 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate city or hub HTML content.")
    parser.add_argument("--topic", required=True, help="Topic slug, e.g. hurricane-impact-ratings-florida.")
    parser.add_argument(
        "--type",
        required=True,
        choices=["hub"],
        help="Content type to generate.",
    )
    parser.add_argument(
        "--notify-discord",
        action="store_true",
        help="Post summary embed to DISCORD_WEBHOOK_URL (same webhook as LangGraph HITL / deploy notices).",
    )
    parser.add_argument(
        "--hitl",
        action="store_true",
        help="Wait for Discord approve/reject (same HITL pattern as city pipeline), then publish hub HTML via worker.",
    )
    args = parser.parse_args()

    if args.type == "hub":
        if args.hitl and args.notify_discord:
            print("Note: --hitl already sends the full review webhook; skipping extra --notify-discord.", flush=True)
        if args.hitl:
            raise SystemExit(run_hub_with_hitl(args.topic))
        out_path = generate_hub(args.topic, notify_discord=args.notify_discord)
        print(f"Hub page generated: {out_path}")


if __name__ == "__main__":
    main()
