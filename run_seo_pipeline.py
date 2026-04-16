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

from agents.orchestrator import compile_seo_app


def _slugify_city(city: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", city.strip().lower()).strip("_")
    return s or "output"


def main() -> None:
    thread_id = str(uuid.uuid4())
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    app = compile_seo_app()

    print(f"[pipeline] thread_id={thread_id}  (use with resume_hitl.py if HITL pauses)\n")

    city = "Boca Raton"
    inputs: Any = {"city": city}

    while True:
        interrupted = False
        for chunk in app.stream(inputs, cfg):
            if isinstance(chunk, dict) and "__interrupt__" in chunk:
                interrupted = True
                break
        if interrupted:
            auto = os.getenv("AUTO_APPROVE_HITL", "true").lower() in ("1", "true", "yes")
            if auto:
                print("[HITL] AUTO_APPROVE_HITL=true → resuming with publish=True\n")
                inputs = Command(resume={"publish": True})
                continue
            print(
                "[HITL] Paused. Approve or reject with:\n"
                f'  python resume_hitl.py "{thread_id}" approve\n'
                f'  python resume_hitl.py "{thread_id}" reject\n'
                "Or set AUTO_APPROVE_HITL=true and re-run.\n"
            )
            raise SystemExit(2)
        break

    snap = app.get_state(cfg)
    final_state = snap.values

    draft = (final_state.get("content_draft") or "").strip()
    print(draft)

    clean_dir = ROOT / "data" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = _slugify_city(city)
    out_path = clean_dir / f"{slug}_pipeline_{stamp}.html"
    out_path.write_text(draft if draft else "<!-- empty content_draft -->\n", encoding="utf-8")
    print(f"\nSaved HTML: {out_path.relative_to(ROOT)}")
    pr = final_state.get("publish_result")
    if pr is not None:
        print(f"publish_result: {pr}")


if __name__ == "__main__":
    main()
