"""Shared Discord helpers for SEO agent notifications and HITL approvals."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

DEFAULT_AGENT_NAME = "Mark"
DEFAULT_HITL_CHANNEL_ID = "1495190959405924574"


def agent_name() -> str:
    """Return the AI agent label used inside Discord messages."""
    return os.getenv("SEO_DISCORD_AGENT_NAME", DEFAULT_AGENT_NAME).strip() or DEFAULT_AGENT_NAME


def agent_footer(*parts: str) -> str:
    """Build a consistent footer that keeps the Mark agent label visible."""
    clean_parts = [agent_name(), *(part.strip() for part in parts if part.strip())]
    return " | ".join(clean_parts)


def agent_content(message: str) -> str:
    """Prefix message content with the shared AI agent label."""
    return f"**{agent_name()}** - {message}"


def discord_webhook_url() -> str:
    return os.getenv("DISCORD_WEBHOOK_URL", "").strip()


def hitl_channel_id() -> int | None:
    """Return configured HITL channel, defaulting to the approved posting channel."""
    raw = os.getenv("DISCORD_HITL_CHANNEL_ID", DEFAULT_HITL_CHANNEL_ID).strip()
    if not raw:
        raw = DEFAULT_HITL_CHANNEL_ID
    try:
        return int(raw)
    except ValueError:
        return int(DEFAULT_HITL_CHANNEL_ID)


def post_discord_payload(payload: dict[str, Any], webhook_url: str | None = None, timeout: float = 30.0) -> bool:
    """Post a full Discord webhook payload and return whether Discord accepted it."""
    url = (webhook_url or discord_webhook_url()).strip()
    if not url or url == "PASTE_WEBHOOK":
        return False
    try:
        response = httpx.post(url, json=payload, timeout=timeout)
    except httpx.HTTPError:
        return False
    return response.is_success


def post_to_discord(
    webhook_url: str,
    content: str,
    *,
    embeds: list[dict[str, Any]] | None = None,
    username: str | None = None,
    timeout: float = 30.0,
) -> bool:
    """Job-scraper-compatible helper for simple Discord webhook posts."""
    payload: dict[str, Any] = {"content": content}
    if embeds:
        payload["embeds"] = embeds
    if username:
        payload["username"] = username
    return post_discord_payload(payload, webhook_url=webhook_url, timeout=timeout)
