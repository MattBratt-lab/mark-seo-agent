"""Content Agent processor for cleaning SEO raw data with Google Gemma 4.

Uses the ``ollama`` Python library against ``OLLAMA_HOST`` (default ``http://localhost:11434``)
with ``GEMMA_MODEL`` (default ``gemma4:e4b``). Install the weights first, e.g.
``ollama pull gemma4:e4b`` or ``ollama pull gemma4``, then set ``GEMMA_MODEL`` to match
``ollama list``. Output: cleaned JSON report under ``/data/clean``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from ollama import Client


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
CLEAN_DIR = ROOT_DIR / "data" / "clean"

load_dotenv(ROOT_DIR / ".env", override=False)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
# Gemma 4 on Ollama — tag must match `ollama list` (common: gemma4, gemma4:e4b).
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma4:e4b")
TEMPERATURE = 1.0
TOP_P = 0.95


def _get_ollama_client() -> Client:
    """Initialize the Ollama SDK client."""
    return Client(host=OLLAMA_HOST)


def _resolve_raw_file(input_file: str) -> Path:
    """Resolve input path safely under /data/raw."""
    candidate = (RAW_DIR / input_file).resolve()
    raw_root = RAW_DIR.resolve()
    if raw_root not in candidate.parents and candidate != raw_root:
        raise ValueError("input_file must resolve inside /data/raw")
    if not candidate.exists():
        raise FileNotFoundError(f"Raw input file not found: {candidate}")
    if not candidate.is_file():
        raise ValueError(f"input_file is not a file: {candidate}")
    return candidate


def _ask_gemma_to_clean(raw_text: str) -> Dict[str, Any]:
    """Ask Gemma 4 to remove HTML and return structured SEO-safe JSON."""
    client = _get_ollama_client()
    response = client.chat(
        model=GEMMA_MODEL,
        options={"temperature": TEMPERATURE, "top_p": TOP_P},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a content cleaning assistant. "
                    "Use <|think|> internally for reasoning if supported, "
                    "but return only final JSON output with no chain-of-thought. "
                    "Return valid JSON with keys: cleaned_text, summary, word_count."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Input may be JSON from a Firecrawl search export or HTML. "
                    "Extract useful titles, URLs, and snippets for SEO research. "
                    "Strip tags and noise; preserve readable structure. "
                    "Return only JSON with keys: cleaned_text, summary, word_count.\n\n"
                    f"{raw_text}"
                ),
            },
        ],
        format="json",
    )

    content = response["message"]["content"]
    parsed = json.loads(content)
    if "cleaned_text" not in parsed:
        raise ValueError("Gemma response missing required key: cleaned_text")
    return parsed


def build_clean_report(raw_text: str, *, source_file_rel: str) -> Dict[str, Any]:
    """Run Gemma via Ollama on raw text; return the report dict (no file write)."""
    cleaned = _ask_gemma_to_clean(raw_text)
    return {
        "agent": "Content Agent",
        "model": GEMMA_MODEL,
        "config": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "think_token_enabled": True,
        },
        "source_file": source_file_rel,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": cleaned,
    }


def clean_seo_data(input_file: str) -> Path:
    """Read raw file, clean with Gemma, and write JSON report to /data/clean.

    Args:
        input_file: File path relative to /data/raw (example: "page.html").

    Returns:
        Path to the generated report file in /data/clean.
    """
    raw_file = _resolve_raw_file(input_file)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    raw_content = raw_file.read_text(encoding="utf-8", errors="ignore")
    report = build_clean_report(raw_content, source_file_rel=str(raw_file.relative_to(ROOT_DIR)))

    report_path = CLEAN_DIR / f"{raw_file.stem}_clean_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process raw SEO data with Gemma.")
    parser.add_argument("input_file", help="File name relative to /data/raw (example: page.html)")
    args = parser.parse_args()

    output_path = clean_seo_data(args.input_file)
    print(f"Clean report created: {output_path}")

