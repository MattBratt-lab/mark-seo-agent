"""Human-in-the-loop notifications (Discord webhook and/or Resend email)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)


def _truncate(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n - 3] + "..."


def notify_human_review(
    *,
    city: str,
    content_draft: str,
    thread_id: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Notify operator with draft excerpt and resume instructions for LangGraph ``Command``."""
    preview = _truncate(content_draft, 4000)
    body_lines = [
        "## SEO Factory — publish review",
        f"**City:** {city}",
        f"**Thread ID:** `{thread_id}`",
        "",
        "Resume from another terminal (SQLite checkpoint in `data/checkpoints.sqlite`):",
        "```bash",
        f'python resume_hitl.py "{thread_id}" approve',
        f'# python resume_hitl.py "{thread_id}" reject',
        "```",
        "Or in Python: `app.invoke(Command(resume={\"publish\": True}), cfg)` with the same `thread_id`.",
        "",
        "### Draft preview",
        preview,
    ]
    if extra:
        body_lines.extend(["", "### Context", str(extra)[:1500]])

    text = "\n".join(body_lines)

    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if webhook:
        payload: dict[str, Any] = {
            "content": _truncate(f"**HITL** — {city} — thread `{thread_id}`", 1900),
            "embeds": [
                {
                    "title": "Draft preview (truncated)",
                    "description": _truncate(preview, 3500),
                    "color": 0x5865F2,
                }
            ],
        }
        httpx.post(webhook, json=payload, timeout=30.0)

    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    from_addr = os.getenv("RESEND_FROM_EMAIL", "").strip()
    to_addr = os.getenv("HITL_NOTIFY_EMAIL", "").strip()
    if resend_key and from_addr and to_addr:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
            json={
                "from": from_addr,
                "to": [to_addr],
                "subject": f"[SEO Factory] Review publish — {city}",
                "html": f"<pre style='white-space:pre-wrap;font-family:monospace'>{_html_escape(text)}</pre>",
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
