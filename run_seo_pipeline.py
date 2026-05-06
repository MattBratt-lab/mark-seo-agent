"""Run the LangGraph SEO pipeline end-to-end and persist the final HTML draft."""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langgraph.types import Command

ROOT = Path(__file__).resolve().parent


def _load_dotenv_safe() -> None:
    env_path = ROOT / ".env"
    try:
        load_dotenv(env_path, override=False)
    except ValueError as exc:
        if "null" in str(exc).lower():
            raise SystemExit(
                f"Invalid {env_path}: embedded NUL bytes (common if the file was saved as UTF-16 "
                "or keys were pasted from a source that inserted wide characters). "
                "Replace the file with a plain UTF-8 copy of .env.template, then add KEY=value lines "
                "in VS Code / Notepad (UTF-8) without Unicode spaces.\n"
                f"Original error: {exc}"
            ) from exc
        raise


_load_dotenv_safe()

from agents.discord_bridge import agent_content, agent_footer, discord_webhook_url, post_discord_payload
from agents.orchestrator import compile_seo_app
from agents.discord_hitl_bot import start_bot_in_thread


def _notify_deploy_result(city: str, commit_url: str, file_path: str, pages_ok: bool) -> None:
    webhook = discord_webhook_url()
    if not webhook:
        return
    status_icon = "✅" if pages_ok else "⚠️"
    slug = re.sub(r"[^\w\-]+", "-", city.strip().lower()).strip("-")
    live_url = f"https://www.dandbgaragedoors.com/locations/{slug}/"
    payload = {
        "username": "D&B SEO Orchestrator",
        "content": agent_content(f"Deploy result — {city}"),
        "embeds": [
            {
                "title": f"{status_icon} Deployed — {city}",
                "color": 0x2ECC71 if pages_ok else 0xE74C3C,
                "fields": [
                    {"name": "🌐 Live Page", "value": live_url, "inline": False},
                    {"name": "📄 File", "value": f"`{file_path}`", "inline": False},
                    {"name": "🔗 Commit", "value": commit_url, "inline": False},
                ],
                "footer": {"text": agent_footer("SEO Factory", "D&B Garage Doors")},
            }
        ],
    }
    if not post_discord_payload(payload, webhook_url=webhook, timeout=15.0):
        print("  [Discord] Deploy notification failed or was rejected.")


def _slugify_city(city: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", city.strip().lower()).strip("_")
    return s or "output"


CITIES = [
    "Boca Raton",
    "Highland Beach",
    "Delray Beach",
    "Gulf Stream",
    "Ocean Ridge",
    "Briny Breezes",
    "Boynton Beach",
    "Hypoluxo",
    "Manalapan",
    "Lantana",
    "South Palm Beach",
    "Palm Beach",
    "Lake Worth",
    "Lake Clarke Shores",
    "Palm Springs",
    "Greenacres",
    "Atlantis",
    "Wellington",
    "Royal Palm Beach",
    "West Palm Beach",
    "Haverhill",
    "Cloud Lake",
    "Glen Ridge",
    "Riviera Beach",
    "Mangonia Park",
    "Palm Beach Gardens",
    "North Palm Beach",
    "Lake Park",
    "Juno Beach",
    "Jupiter",
    "Tequesta",
]


def _selected_cities() -> list[str]:
    raw = os.getenv("SEO_CITY", "").strip()
    if not raw:
        return CITIES
    wanted = {part.strip().lower() for part in raw.split(",") if part.strip()}
    selected = [city for city in CITIES if city.lower() in wanted]
    if selected:
        return selected
    return [part.strip() for part in raw.split(",") if part.strip()]


def _run_city(app: Any, city: str) -> dict[str, Any]:
    thread_id = str(uuid.uuid4())
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    print(f"\n{'='*50}")
    print(f"  Processing: {city}")
    print(f"{'='*50}")

    inputs: Any = {"city": city}
    while True:
        interrupted = False
        for chunk in app.stream(inputs, cfg):
            if isinstance(chunk, dict) and "__interrupt__" in chunk:
                interrupted = True
                break
        if interrupted:
            auto = os.getenv("AUTO_APPROVE_HITL", "false").lower() in ("1", "true", "yes")
            if auto:
                inputs = Command(resume={"publish": True})
                continue

            # Wait for Discord button click (or slash command) to resolve approval.
            from agents import hitl_gate
            event = hitl_gate.register(thread_id)
            timeout = int(os.getenv("HITL_TIMEOUT_SECONDS", "3600"))
            print(f"[HITL] Waiting for Discord approval — click ✅/❌ in Discord (timeout: {timeout}s).")
            print(f"[HITL] Thread ID: {thread_id}")
            resolved = event.wait(timeout=timeout)
            if not resolved:
                print("[HITL] Timed out — skipping publish.")
                inputs = Command(resume={"publish": False})
            else:
                approved = hitl_gate.pop_result(thread_id)
                print(f"[HITL] {'Approved ✅' if approved else 'Rejected ❌'}")
                inputs = Command(resume={"publish": approved})
            continue
        break

    return app.get_state(cfg).values


def main() -> None:
    # Start Discord bot in background thread so button approvals work without a separate process.
    start_bot_in_thread()

    app = compile_seo_app()

    clean_dir = ROOT / "data" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    for city in _selected_cities():
        final_state = _run_city(app, city)

        draft = (final_state.get("content_draft") or "").strip()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = _slugify_city(city)
        out_path = clean_dir / f"{slug}_pipeline_{stamp}.html"
        out_path.write_text(draft if draft else "<!-- empty content_draft -->\n", encoding="utf-8")

        pr = final_state.get("publish_result") or {}
        deploy = pr.get("deploy", {})
        local = pr.get("local_deploy", {})
        commit_url = deploy.get("commitUrl", "—")
        file_path = deploy.get("filePath", "—")
        pages_ok = local.get("returncode") == 0

        print(f"  File    : {file_path}")
        print(f"  Commit  : {commit_url}")
        print(f"  Pages   : {'✓ deployed' if pages_ok else '✗ skipped/failed'}")
        print(f"  Saved   : {out_path.relative_to(ROOT)}")

        # Only notify Discord when something actually deployed (not when HITL was skipped/timed out)
        if commit_url != "—":
            _notify_deploy_result(city, commit_url, file_path, pages_ok)


if __name__ == "__main__":
    main()
