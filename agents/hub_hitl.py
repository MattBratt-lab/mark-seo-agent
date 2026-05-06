"""Hub page HITL: persist pending publish so Discord (same or separate process) can approve/reject."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
PENDING_DIR = ROOT / "data" / "hub_hitl_pending"


def _pending_path(thread_id: str) -> Path:
    return PENDING_DIR / f"{thread_id}.json"


def _resolved_path(thread_id: str) -> Path:
    return PENDING_DIR / f"{thread_id}_resolved.json"


def save_hub_pending(thread_id: str, *, topic: str, hub_slug: str, html_path: Path) -> None:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    rel = html_path
    try:
        rel = html_path.relative_to(ROOT)
    except ValueError:
        pass
    payload = {
        "topic": topic,
        "hub_slug": hub_slug,
        "html_relative": str(rel).replace("\\", "/"),
    }
    _pending_path(thread_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_hub_pending(thread_id: str) -> None:
    _pending_path(thread_id).unlink(missing_ok=True)
    _resolved_path(thread_id).unlink(missing_ok=True)


def _write_resolved(thread_id: str, payload: dict[str, Any]) -> None:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    _resolved_path(thread_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def try_resolve_hub_hitl(thread_id: str, *, approved: bool) -> dict[str, Any] | None:
    """If this thread_id is a pending hub publish, handle approve/reject and return a result dict.

    Always writes ``{thread_id}_resolved.json`` when a pending file existed so a waiting
    ``writer_node --hitl`` process can unblock (even if publish throws).

    Returns ``None`` if there is no hub pending for this thread (caller should try LangGraph resume).
    """
    pending = _pending_path(thread_id)
    if not pending.exists():
        return None

    try:
        meta = json.loads(pending.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pending.unlink(missing_ok=True)
        return None

    topic = str(meta.get("topic", ""))
    hub_slug = str(meta.get("hub_slug", ""))
    rel = str(meta.get("html_relative", ""))
    html_path = ROOT / rel if rel else ROOT

    if not approved:
        pending.unlink(missing_ok=True)
        _write_resolved(thread_id, {"approved": False})
        return {"kind": "hub", "approved": False, "skipped": True, "reason": "hub_rejected"}

    if not html_path.is_file():
        pending.unlink(missing_ok=True)
        msg = f"hub html missing: {html_path}"
        _write_resolved(thread_id, {"approved": False, "error": msg})
        return {"kind": "hub", "approved": False, "error": msg}

    publish_result: dict[str, Any] = {"ok": False, "error": "publish_not_run"}
    try:
        html = html_path.read_text(encoding="utf-8")
        publish_result = publish_hub_to_worker(html, hub_slug=hub_slug, topic=topic)
    except Exception as exc:
        publish_result = {"ok": False, "error": str(exc)}
    finally:
        pending.unlink(missing_ok=True)

    # Unblock writer_node --hitl even if GitHub/worker failed (result is in publish_result).
    _write_resolved(thread_id, {"approved": True, "publish_result": publish_result})
    return {"kind": "hub", "approved": True, "publish_result": publish_result}


def consume_resolved(thread_id: str) -> dict[str, Any] | None:
    """If cross-process Discord wrote a resolution file, read and remove it."""
    rp = _resolved_path(thread_id)
    if not rp.exists():
        return None
    try:
        data = json.loads(rp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        rp.unlink(missing_ok=True)
        return None
    rp.unlink(missing_ok=True)
    return data


def publish_hub_to_worker(html: str, *, hub_slug: str, topic: str) -> dict[str, Any]:
    """POST hub HTML to the publish worker (raw HTML path under ``guides/``)."""
    worker_url = (os.getenv("PUBLISH_WORKER_URL") or "").strip().rstrip("/")
    token = (os.getenv("PUBLISH_AUTH_TOKEN") or os.getenv("AUTH_TOKEN") or "").strip()
    if not worker_url or not token:
        return {
            "skipped": True,
            "reason": "Set PUBLISH_WORKER_URL and PUBLISH_AUTH_TOKEN (worker secret AUTH_TOKEN).",
        }

    safe_slug = hub_slug.strip() or "hub-page"
    target_path = (
        os.getenv("HUB_PUBLISH_TARGET_PREFIX", "guides").strip().strip("/")
        + f"/{safe_slug}/index.html"
    )

    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                f"{worker_url}/publish",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "html": html,
                    "hubSlug": safe_slug,
                    "city": f"Hub: {topic}",
                    "markdown": " ",
                    "targetPath": target_path,
                },
            )
            r.raise_for_status()
            body = r.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return body if isinstance(body, dict) else {"raw": body}
