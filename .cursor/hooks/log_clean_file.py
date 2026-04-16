#!/usr/bin/env python3
"""Hook: append workflow log when /data/clean files are written."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = (ROOT / "data" / "clean").resolve()
WORKFLOW_FILE = ROOT / "docs" / "workflow_state.md"


def _extract_candidate_paths(payload: dict) -> list[Path]:
    candidates: list[str] = []
    for key in ("file_path", "path", "target_file", "filepath"):
        value = payload.get(key)
        if isinstance(value, str):
            candidates.append(value)

    for key in ("file_paths", "paths", "edited_files"):
        value = payload.get(key)
        if isinstance(value, list):
            candidates.extend([item for item in value if isinstance(item, str)])

    return [Path(p).resolve() for p in candidates]


def main() -> int:
    raw_input = sys.stdin.read()
    try:
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except json.JSONDecodeError:
        print("{}")
        return 0

    matches = []
    for p in _extract_candidate_paths(payload):
        if p == CLEAN_DIR or CLEAN_DIR in p.parents:
            matches.append(p)

    if not matches:
        print("{}")
        return 0

    WORKFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not WORKFLOW_FILE.exists():
        WORKFLOW_FILE.write_text(
            "Current State: [Initialization]\nGoal: Build SEO Agent Team\nLog:\n",
            encoding="utf-8",
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    filename = matches[0].name
    with WORKFLOW_FILE.open("a", encoding="utf-8") as f:
        f.write(
            f"- [{timestamp}] - Auto-log: detected clean data file update `{filename}` in /data/clean.\n"
        )

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
