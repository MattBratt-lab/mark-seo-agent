"""Discord bot: slash commands + ✅/❌ buttons to approve or reject LangGraph HITL publishes.

Requires a Discord *application bot* token (not the webhook). Run on the same machine that
hosts ``data/checkpoints.sqlite`` so ``compile_seo_app()`` can resume the right thread.

Setup (summary):
1. Discord Developer Portal → Application → Bot → reset token → ``DISCORD_BOT_TOKEN``.
2. OAuth2 → URL Generator: ``bot`` + ``applications.commands``; invite to your server.
3. Set ``DISCORD_HITL_CHANNEL_ID`` to the channel where button messages will be sent
   (defaults to ``1495190959405924574``).
4. Optionally set ``DISCORD_HITL_GUILD_ID`` for fast guild command sync.
5. Set approvers via ``DISCORD_HITL_APPROVER_USER_IDS`` and/or ``DISCORD_HITL_APPROVER_ROLE_IDS``
   (if both empty, only members with **Manage Server** may run the commands).

Run from repo root: ``python agents/discord_hitl_bot.py``
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Callable, TypeVar

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=False)

from agents.discord_bridge import DEFAULT_HITL_CHANNEL_ID, agent_content, hitl_channel_id

_F = TypeVar("_F", bound=Callable[..., Any])


def _parse_snowflakes(raw: str) -> set[int]:
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return out


def _approver_user_ids() -> set[int]:
    return _parse_snowflakes(os.getenv("DISCORD_HITL_APPROVER_USER_IDS", ""))


def _approver_role_ids() -> set[int]:
    return _parse_snowflakes(os.getenv("DISCORD_HITL_APPROVER_ROLE_IDS", ""))


def _member_allowed(member: discord.Member) -> bool:
    users = _approver_user_ids()
    roles = _approver_role_ids()
    if member.id in users:
        return True
    if roles and any(r.id in roles for r in member.roles):
        return True
    if not users and not roles:
        return member.guild_permissions.manage_guild
    return False


def _guild_id() -> int | None:
    raw = os.getenv("DISCORD_HITL_GUILD_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _channel_id() -> int | None:
    return hitl_channel_id()


def _resume_hitl(*, thread_id: str, publish: bool) -> dict:
    from agents.orchestrator import compile_seo_app

    cfg = {"configurable": {"thread_id": thread_id}}
    app = compile_seo_app()
    for _ in app.stream(__import__("langgraph.types", fromlist=["Command"]).Command(resume={"publish": publish}), cfg):
        pass
    snap = app.get_state(cfg)
    return {
        "publish_result": snap.values.get("publish_result"),
        "publish_approved": snap.values.get("publish_approved"),
    }


async def _run_resume(thread_id: str, publish: bool) -> dict:
    return await asyncio.to_thread(_resume_hitl, thread_id=thread_id, publish=publish)


class ApprovalView(ui.View):
    """Persistent button row for approving or rejecting a single HITL thread."""

    def __init__(self, thread_id: str, city: str = "") -> None:
        super().__init__(timeout=None)
        self.thread_id = thread_id
        self.city = city
        # Encode thread_id in custom_id so it survives bot restarts
        self.approve_button.custom_id = f"hitl_approve:{thread_id}"
        self.reject_button.custom_id = f"hitl_reject:{thread_id}"

    @ui.button(label="✅ Approve — Push to Website", style=discord.ButtonStyle.success, custom_id="hitl_approve:placeholder")
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await self._handle(interaction, approved=True)

    @ui.button(label="❌ Reject — Skip", style=discord.ButtonStyle.danger, custom_id="hitl_reject:placeholder")
    async def reject_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await self._handle(interaction, approved=False)

    async def _handle(self, interaction: discord.Interaction, *, approved: bool) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return
        if not _member_allowed(interaction.user):
            await interaction.response.send_message("You are not authorized to approve publishes.", ephemeral=True)
            return

        await interaction.response.defer()

        # Try in-process gate first (pipeline running in same process)
        from agents import hitl_gate
        resolved = hitl_gate.resolve(self.thread_id, approved=approved)

        if not resolved:
            from agents import hub_hitl

            # Hub publish does sync HTTP — must not block the discord.py event loop (freezes buttons / "stuck").
            hub_out = await asyncio.to_thread(
                lambda: hub_hitl.try_resolve_hub_hitl(self.thread_id, approved=approved)
            )
            if hub_out is not None:
                if approved:
                    pr = hub_out.get("publish_result") or {}
                    dep = pr.get("deploy") if isinstance(pr, dict) else {}
                    commit = (dep or {}).get("commitUrl", "—") if isinstance(dep, dict) else "—"
                    file_path = (dep or {}).get("filePath", "—") if isinstance(dep, dict) else "—"
                    if pr.get("skipped"):
                        status = f"Hub publish skipped: `{pr.get('reason', pr)}`"
                    elif dep.get("ok") is not True and pr.get("ok") is False:
                        status = f"Hub publish failed.\n`{str(pr.get('error', pr))[:500]}`"
                    else:
                        status = f"Hub published.\n📄 `{file_path}`\n🔗 {commit}"
                else:
                    status = "Hub draft skipped."
            else:
                # LangGraph city pipeline (different process) — do not hang forever on unknown thread_id
                try:
                    result = await asyncio.wait_for(_run_resume(self.thread_id, approved), timeout=90.0)
                    commit = (result.get("publish_result") or {}).get("deploy", {}).get("commitUrl", "—")
                    file_path = (result.get("publish_result") or {}).get("deploy", {}).get("filePath", "—")
                    if approved:
                        status = f"📄 `{file_path}`\n🔗 {commit}"
                    else:
                        status = "Page skipped."
                except asyncio.TimeoutError:
                    status = (
                        "No hub pending file and LangGraph resume timed out. "
                        "If this was a **hub** run, use the same machine as `writer_node --hitl` or run:\n"
                        f"`python resume_hub_hitl.py {self.thread_id} reject`"
                    )
                except Exception as exc:
                    status = f"Resume error: `{str(exc)[:300]}`"
        else:
            if approved:
                status = "Pipeline notified — deploying now... (check Discord for commit URL)"
            else:
                status = "Page skipped."

        label = "✅ Approved" if approved else "❌ Rejected"
        content = f"**{label}** by {interaction.user.mention} — **{self.city or self.thread_id}**\n{status}"
        try:
            await interaction.edit_original_response(content=content[:2000], view=None)
        except Exception:
            if interaction.message:
                await interaction.message.edit(content=content[:2000], view=None)
            else:
                await interaction.followup.send(content=content[:2000], ephemeral=True)
        self.stop()


def _intents() -> discord.Intents:
    intents = discord.Intents.default()
    if _approver_role_ids():
        intents.members = True
    return intents


class HitlBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=_intents())

    async def on_ready(self) -> None:
        user = self.user
        name = getattr(user, "name", "?") if user else "?"
        uid = getattr(user, "id", 0) if user else 0
        print(f"[discord_hitl_bot] Logged in as {name} (id={uid})", flush=True)
        ch = _channel_id()
        if ch:
            print(f"[discord_hitl_bot] Button messages → channel {ch}", flush=True)
        else:
            print(
                f"[discord_hitl_bot] DISCORD_HITL_CHANNEL_ID invalid — expected channel {DEFAULT_HITL_CHANNEL_ID}.",
                flush=True,
            )
        self._send_buttons_task.start()

    async def setup_hook(self) -> None:
        gid = _guild_id()
        guild_obj = discord.Object(id=gid) if gid is not None else None
        guild_scope: list[discord.Object] = [guild_obj] if guild_obj is not None else []

        def _scope_decorator(fn: _F) -> _F:
            if guild_scope:
                return app_commands.guilds(*guild_scope)(fn)  # type: ignore[return-value]
            return fn

        @_scope_decorator
        @self.tree.command(name="hitl-approve", description="Approve SEO publish for a HITL thread")
        @app_commands.describe(thread_id="Thread ID from the HITL Discord message")
        async def hitl_approve(interaction: discord.Interaction, thread_id: str) -> None:
            if not interaction.guild or not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Use this command in a server.", ephemeral=True)
                return
            if not _member_allowed(interaction.user):
                await interaction.response.send_message("You are not allowed to approve publishes.", ephemeral=True)
                return
            tid = thread_id.strip()
            if not tid:
                await interaction.response.send_message("thread_id is empty.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True, thinking=True)
            from agents import hitl_gate
            resolved = hitl_gate.resolve(tid, approved=True)
            if resolved:
                await interaction.followup.send("Approved — pipeline will resume.", ephemeral=True)
            else:
                from agents import hub_hitl

                hub_out = await asyncio.to_thread(lambda: hub_hitl.try_resolve_hub_hitl(tid, approved=True))
                if hub_out is not None:
                    pr = hub_out.get("publish_result") or {}
                    dep = pr.get("deploy") if isinstance(pr, dict) else {}
                    commit = (dep or {}).get("commitUrl", "—") if isinstance(dep, dict) else "—"
                    file_path = (dep or {}).get("filePath", "—") if isinstance(dep, dict) else "—"
                    if pr.get("skipped"):
                        msg = f"Hub publish skipped: `{pr.get('reason', pr)}`"
                    elif dep.get("ok") is not True and pr.get("ok") is False:
                        msg = f"Hub publish failed: `{str(pr.get('error', pr))[:400]}`"
                    else:
                        msg = f"✅ Hub approved & deployed\n📄 `{file_path}`\n🔗 {commit}"
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    try:
                        result = await asyncio.wait_for(_run_resume(tid, True), timeout=90.0)
                        commit = (result.get("publish_result") or {}).get("deploy", {}).get("commitUrl", "—")
                        file_path = (result.get("publish_result") or {}).get("deploy", {}).get("filePath", "—")
                        await interaction.followup.send(
                            f"✅ Approved & deployed\n📄 File: `{file_path}`\n🔗 Commit: {commit}",
                            ephemeral=True,
                        )
                    except asyncio.TimeoutError:
                        await interaction.followup.send(
                            f"LangGraph resume timed out (no checkpoint for `{tid}`?). "
                            f"If this was a hub, run: `python resume_hub_hitl.py {tid} reject`",
                            ephemeral=True,
                        )
                    except Exception as exc:
                        await interaction.followup.send(f"Resume failed: `{str(exc)[:300]}`", ephemeral=True)

        @_scope_decorator
        @self.tree.command(name="hitl-reject", description="Reject SEO publish for a HITL thread")
        @app_commands.describe(thread_id="Thread ID from the HITL Discord message")
        async def hitl_reject(interaction: discord.Interaction, thread_id: str) -> None:
            if not interaction.guild or not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Use this command in a server.", ephemeral=True)
                return
            if not _member_allowed(interaction.user):
                await interaction.response.send_message("You are not allowed to reject publishes.", ephemeral=True)
                return
            tid = thread_id.strip()
            if not tid:
                await interaction.response.send_message("thread_id is empty.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True, thinking=True)
            from agents import hitl_gate
            resolved = hitl_gate.resolve(tid, approved=False)
            if resolved:
                await interaction.followup.send("❌ Rejected — pipeline will skip this city.", ephemeral=True)
            else:
                from agents import hub_hitl

                hub_out = await asyncio.to_thread(lambda: hub_hitl.try_resolve_hub_hitl(tid, approved=False))
                if hub_out is not None:
                    await interaction.followup.send("❌ Hub draft rejected — skipped.", ephemeral=True)
                else:
                    try:
                        await asyncio.wait_for(_run_resume(tid, False), timeout=90.0)
                        await interaction.followup.send("❌ Rejected — page skipped.", ephemeral=True)
                    except asyncio.TimeoutError:
                        await interaction.followup.send(
                            f"LangGraph reject timed out for `{tid}`. "
                            f"If this was only a hub run, run: `python resume_hub_hitl.py {tid} reject`",
                            ephemeral=True,
                        )
                    except Exception as exc:
                        await interaction.followup.send(f"Resume failed: `{str(exc)[:300]}`", ephemeral=True)

        if guild_obj is not None:
            await self.tree.sync(guild=guild_obj)
        else:
            await self.tree.sync()

    @tasks.loop(seconds=1)
    async def _send_buttons_task(self) -> None:
        """Poll hitl_gate queue and send button messages to channel, with DM fallback."""
        from agents import hitl_gate
        msg = hitl_gate.dequeue_button_message()
        if msg is None:
            return
        city, thread_id = msg
        view = ApprovalView(thread_id=thread_id, city=city)
        content = agent_content(f"Publish ready for {city} — click to approve or reject:")

        # Try configured channel first
        ch_id = _channel_id()
        sent = False
        if ch_id:
            try:
                channel = await self.fetch_channel(ch_id)
                await channel.send(content, view=view)  # type: ignore[union-attr]
                print(f"[discord_hitl_bot] Button sent to channel for {city}", flush=True)
                sent = True
            except discord.Forbidden:
                print(f"[discord_hitl_bot] Channel {ch_id} forbidden — trying DM fallback.", flush=True)
            except Exception as exc:
                print(f"[discord_hitl_bot] Channel error: {exc} — trying DM fallback.", flush=True)

        # DM fallback — message every configured approver directly
        if not sent:
            approver_ids = _approver_user_ids()
            for uid in approver_ids:
                try:
                    user = await self.fetch_user(uid)
                    dm = await user.create_dm()
                    await dm.send(content, view=view)
                    print(f"[discord_hitl_bot] Button sent via DM to user {uid} for {city}", flush=True)
                    sent = True
                except Exception as exc:
                    print(f"[discord_hitl_bot] DM to {uid} failed: {exc}", flush=True)

        if not sent:
            print(
                f"[discord_hitl_bot] WARNING: Could not send buttons for {city}. "
                "Fix channel permissions or set DISCORD_HITL_APPROVER_USER_IDS in .env.",
                flush=True,
            )

    @_send_buttons_task.before_loop
    async def _before_send_task(self) -> None:
        await self.wait_until_ready()


def start_bot_in_thread() -> None:
    """Start the Discord bot in a daemon thread (call from run_seo_pipeline.py)."""
    import threading

    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print("[discord_hitl_bot] DISCORD_BOT_TOKEN not set — Discord button approvals disabled.", flush=True)
        return

    def _run() -> None:
        try:
            HitlBot().run(token, log_handler=None)
        except discord.LoginFailure:
            print("[discord_hitl_bot] Login failed: invalid DISCORD_BOT_TOKEN.", file=sys.stderr)

    t = threading.Thread(target=_run, daemon=True, name="discord-hitl-bot")
    t.start()
    print("[discord_hitl_bot] Bot thread started.", flush=True)


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print("Set DISCORD_BOT_TOKEN in .env (Discord application bot token).", file=sys.stderr)
        raise SystemExit(1)
    print("[discord_hitl_bot] Connecting to Discord…", flush=True)
    try:
        HitlBot().run(token)
    except discord.LoginFailure:
        print(
            "[discord_hitl_bot] Login failed: invalid DISCORD_BOT_TOKEN. "
            "Create a new bot token in the Developer Portal and update .env.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
