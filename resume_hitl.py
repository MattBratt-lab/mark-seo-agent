"""Resume a paused HITL gate (same thread_id as printed by run_seo_pipeline.py)."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from langgraph.types import Command

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

from agents.orchestrator import compile_seo_app


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python resume_hitl.py <THREAD_ID> approve|reject")
        raise SystemExit(2)
    thread_id = sys.argv[1]
    verdict = sys.argv[2].lower()
    publish = verdict in ("approve", "approved", "true", "1", "yes", "y")

    cfg = {"configurable": {"thread_id": thread_id}}
    app = compile_seo_app()
    for _ in app.stream(Command(resume={"publish": publish}), cfg):
        pass
    snap = app.get_state(cfg)
    print("publish_result:", snap.values.get("publish_result"))
    print("Done.")


if __name__ == "__main__":
    main()
