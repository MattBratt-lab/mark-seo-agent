"""Thread-safe gate: connects the running Discord bot to the paused LangGraph pipeline."""

from __future__ import annotations

import queue
import threading
from typing import Any

# Pending approvals: thread_id -> {"event": Event, "approved": bool}
_pending: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()

# Queue of button messages for the bot to send: (city, thread_id)
_send_queue: queue.Queue[tuple[str, str]] = queue.Queue()


def register(thread_id: str) -> threading.Event:
    """Register a pending approval. Call event.wait() to block until resolved."""
    event = threading.Event()
    with _lock:
        _pending[thread_id] = {"event": event, "approved": False}
    return event


def resolve(thread_id: str, *, approved: bool) -> bool:
    """Resolve a pending approval from the Discord bot. Returns False if not found."""
    with _lock:
        entry = _pending.get(thread_id)
    if not entry:
        return False
    entry["approved"] = approved
    entry["event"].set()
    return True


def pop_result(thread_id: str) -> bool:
    """Get the approval result and remove from pending."""
    with _lock:
        return _pending.pop(thread_id, {}).get("approved", False)


def queue_button_message(city: str, thread_id: str) -> None:
    """Ask the Discord bot to send a button message for this city/thread."""
    _send_queue.put((city, thread_id))


def dequeue_button_message(timeout: float = 0.1) -> tuple[str, str] | None:
    """Pull the next queued button message, or None if empty."""
    try:
        return _send_queue.get(timeout=timeout)
    except queue.Empty:
        return None
