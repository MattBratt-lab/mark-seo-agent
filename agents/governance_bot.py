"""Governance / review alerts: post structured Discord webhook messages for content sign-off."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=False)

from agents.discord_bridge import agent_content, agent_footer, discord_webhook_url, post_discord_payload


class GovernanceBot:
    """Send SEO review notifications to Discord via ``DISCORD_WEBHOOK_URL``."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = (webhook_url or discord_webhook_url()).strip()

    def post_to_review(self, city: str, metrics: dict[str, Any] | None = None) -> bool:
        """Send a structured review request to Discord. Returns True if Discord accepted (204)."""
        metrics = metrics or {}
        if not self.webhook_url:
            print("Error: DISCORD_WEBHOOK_URL not set in .env", file=sys.stderr)
            return False

        fixes = str(metrics.get("fixes", "Standard entities applied"))
        rationale = str(metrics.get("rationale", "Optimized for local conversion signals."))
        payload: dict[str, Any] = {
            "username": "D&B SEO Orchestrator",
            "content": agent_content("NEW CONTENT READY FOR REVIEW"),
            "embeds": [
                {
                    "title": f"City page: {city}",
                    "color": 0xF1C40F,
                    "fields": [
                        {"name": "Location", "value": city[:256], "inline": True},
                        {"name": "Gap fixes", "value": fixes[:1024], "inline": True},
                        {"name": "AI rationale", "value": rationale[:1024], "inline": False},
                    ],
                    "footer": {
                        "text": agent_footer("SEO Factory", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
                    },
                }
            ],
        }

        if post_discord_payload(payload, webhook_url=self.webhook_url):
            print(f"Governance alert sent for {city}")
            return True
        print("Discord webhook request failed or was rejected.", file=sys.stderr)
        return False


def main() -> int:
    bot = GovernanceBot()
    ok = bot.post_to_review(
        "Boca Raton",
        {
            "fixes": "Added Clopay entities and 24/7 emergency schema.",
            "rationale": "Matches high-intent SERP gaps identified in Auditor phase.",
        },
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
