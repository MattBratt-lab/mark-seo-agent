"""Unblock a stuck ``writer_node --hitl`` when Discord approve/reject did not wake the CLI.

Writes ``data/hub_hitl_pending/<THREAD_ID>_resolved.json`` so the waiting process can exit.

Usage::

    python resume_hub_hitl.py <THREAD_ID> reject
    python resume_hub_hitl.py <THREAD_ID> approve   # marks approved only; does not publish by itself
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PENDING = ROOT / "data" / "hub_hitl_pending"


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python resume_hub_hitl.py <THREAD_ID> reject|approve")
        return 2
    thread_id = sys.argv[1].strip()
    verdict = sys.argv[2].lower().strip()
    approved = verdict in ("approve", "approved", "true", "1", "yes", "y")

    PENDING.mkdir(parents=True, exist_ok=True)
    resolved = PENDING / f"{thread_id}_resolved.json"
    pending = PENDING / f"{thread_id}.json"
    pending.unlink(missing_ok=True)
    resolved.write_text(json.dumps({"approved": approved, "manual_unblock": True}, indent=2), encoding="utf-8")
    print(f"Wrote {resolved.relative_to(ROOT)} (approved={approved}). The stuck writer should unblock within ~1 second.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
