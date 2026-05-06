"""Publish already-generated HTML pages from data/clean/ to the website.

Use this when the pipeline generated HTML but the HITL gate timed out before publishing.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

CITY_FILES = {
    "Boca Raton":        "boca_raton_pipeline_20260421_033619.html",
    "West Palm Beach":   "west_palm_beach_pipeline_20260421_043735.html",
    "Delray Beach":      "delray_beach_pipeline_20260421_053823.html",
    "Boynton Beach":     "boynton_beach_pipeline_20260421_063943.html",
    "Wellington":        "wellington_pipeline_20260421_074039.html",
    "Jupiter":           "jupiter_pipeline_20260421_084135.html",
    "Palm Beach Gardens":"palm_beach_gardens_pipeline_20260421_094228.html",
    "Lake Worth":        "lake_worth_pipeline_20260421_104337.html",
}

CLEAN_DIR = ROOT / "data" / "clean"


def _html_to_markdown(html: str) -> str:
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", "", t)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|div|h[1-6]|li|tr|section|article)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def publish_city(city: str, html_file: str, *, worker_url: str, token: str) -> dict:
    path = CLEAN_DIR / html_file
    if not path.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    html = path.read_text(encoding="utf-8")
    md = _html_to_markdown(html)

    r = httpx.post(
        f"{worker_url}/publish",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"markdown": md, "city": city},
        timeout=120.0,
    )
    r.raise_for_status()
    return r.json()


def deploy_pages(site_dir: str) -> tuple[bool, str]:
    import subprocess
    subprocess.run(["git", "stash"], cwd=site_dir, capture_output=True)
    subprocess.run(["git", "pull", "--rebase"], cwd=site_dir, capture_output=True)
    subprocess.run(["git", "stash", "pop"], cwd=site_dir, capture_output=True)
    result = subprocess.run(
        ["npx", "wrangler", "pages", "deploy", ".", "--project-name", "db-garage-doors", "--commit-dirty=true"],
        cwd=site_dir, capture_output=True, text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def main() -> None:
    worker_url = os.getenv("PUBLISH_WORKER_URL", "").strip().rstrip("/")
    token = os.getenv("PUBLISH_AUTH_TOKEN", "").strip()
    site_dir = os.getenv("SITE_DIR", "").strip()

    if not worker_url or not token:
        print("ERROR: Set PUBLISH_WORKER_URL and PUBLISH_AUTH_TOKEN in .env")
        sys.exit(1)

    cities = list(CITY_FILES.items())

    # Allow running a single city: python publish_existing.py "Boca Raton"
    if len(sys.argv) > 1:
        name = " ".join(sys.argv[1:])
        cities = [(c, f) for c, f in cities if c.lower() == name.lower()]
        if not cities:
            print(f"Unknown city: {name}. Options: {', '.join(CITY_FILES)}")
            sys.exit(1)

    print(f"Publishing {len(cities)} city page(s)...\n")

    for city, html_file in cities:
        print(f"  [{city}]")
        try:
            body = publish_city(city, html_file, worker_url=worker_url, token=token)
            deploy = body.get("deploy", {})
            commit_url = deploy.get("commitUrl", "—")
            file_path = deploy.get("filePath", "—")
            print(f"    File   : {file_path}")
            print(f"    Commit : {commit_url}")
        except Exception as exc:
            print(f"    ERROR  : {exc}")
            continue

    # Deploy all at once at the end
    if site_dir and os.path.isdir(site_dir):
        print("\nDeploying to Cloudflare Pages...")
        ok, log = deploy_pages(site_dir)
        if ok:
            print("  ✓ Pages deployed successfully")
        else:
            print(f"  ✗ Deploy failed:\n{log[-500:]}")
    else:
        print("\nNote: Set SITE_DIR in .env to also auto-deploy to Cloudflare Pages.")


if __name__ == "__main__":
    main()
