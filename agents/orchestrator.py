"""SEO agent team orchestrator: LangGraph StateGraph with research → parse → write → QA loop."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

# Load repo-root .env for Firecrawl, Google GenAI, and Ollama-related variables.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

# Firecrawl MCP (Cursor): on Windows you can start the MCP server with:
#   cmd /c "set FIRECRAWL_API_KEY=YOUR_KEY_HERE && npx -y firecrawl-mcp"
# This graph's researcher calls the same Firecrawl Search HTTP API the MCP tool uses,
# reading FIRECRAWL_API_KEY from the environment (including .env).
FIRECRAWL_MCP_WINDOWS_HINT = (
    'cmd /c "set FIRECRAWL_API_KEY=YOUR_KEY_HERE && npx -y firecrawl-mcp"'
)


class AgentState(TypedDict, total=False):
    """Shared graph state for the SEO agent pipeline."""

    messages: Annotated[list[AnyMessage], add_messages]
    city: str
    raw_data: str
    raw_input_file: str
    clean_data: dict[str, Any]
    gap_report: dict[str, Any]
    content_draft: str
    publish_approved: bool
    publish_result: dict[str, Any]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_brand_identity() -> dict[str, Any]:
    """Load hardcoded brand identity from ``data/brand_identity.json``."""
    identity_path = _project_root() / "data" / "brand_identity.json"
    if not identity_path.exists():
        return {}
    try:
        return json.loads(identity_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _append_workflow_log(summary: str) -> None:
    log_path = _project_root() / "docs" / "workflow_state.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = f"- [{ts}] - Researcher (Firecrawl search): {summary}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def _firecrawl_search_json(query: str, *, limit: int = 8) -> dict[str, Any]:
    """Run Firecrawl Search (``POST /v1/search``), matching the Firecrawl MCP search tool contract.

    For Cursor MCP on Windows, start the server with the command stored in
    ``FIRECRAWL_MCP_WINDOWS_HINT`` at module scope.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set; cannot run Firecrawl search.")

    base = (os.getenv("FIRECRAWL_BASE_URL") or "https://api.firecrawl.dev").rstrip("/") + "/"
    url = urljoin(base, "v1/search")
    payload: dict[str, Any] = {"query": query, "limit": limit}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            return {"success": False, "error": "Unexpected response shape", "raw": body}
        return body


def researcher_node(state: AgentState) -> dict[str, Any]:
    """Discover sources via Firecrawl Search (MCP-equivalent API); persist JSON under /data/raw."""
    city = (state.get("city") or "unknown").strip()
    query = f"garage door repair {city} FL"

    search_payload = _firecrawl_search_json(query)
    raw_json = json.dumps(search_payload, ensure_ascii=False, indent=2)

    slug = re.sub(r"[^\w\-]+", "_", city.lower()).strip("_")[:80] or "city"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_dir = _project_root() / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_filename = f"research_gdo_{slug}_{stamp}.json"
    raw_path = raw_dir / raw_filename
    raw_path.write_text(raw_json, encoding="utf-8")

    data_block = search_payload.get("data")
    n_results = len(data_block) if isinstance(data_block, list) else 0
    ok = bool(search_payload.get("success", True)) and isinstance(data_block, list)
    _append_workflow_log(
        f"query={query!r}; saved={raw_filename}; success={ok}; results={n_results}"
    )

    msg = AIMessage(
        content=(
            f"Researcher: Firecrawl search for {city!r} ({n_results} results). "
            f"Raw JSON saved to data/raw/{raw_filename}."
        ),
    )
    return {
        "raw_data": raw_json,
        "raw_input_file": raw_filename,
        "messages": [msg],
    }


def gemma_parser_node(state: AgentState) -> dict[str, Any]:
    """Normalize Firecrawl JSON with Ollama — **Google Gemma 4** (``GEMMA_MODEL``, default ``gemma4:e4b``).

    Delegates to ``gemma_processor.clean_seo_data`` (``ollama`` client + Gemma 4), writes
    ``*_clean_report.json`` under ``/data/clean``, and loads the full report into ``clean_data``.
    """
    from agents.gemma_processor import clean_seo_data

    raw_file = state.get("raw_input_file")
    if not raw_file:
        raise ValueError("gemma_parser_node requires state['raw_input_file'] from researcher_node.")

    report_path = clean_seo_data(raw_file)
    report: dict[str, Any] = json.loads(report_path.read_text(encoding="utf-8"))

    msg = AIMessage(
        content=(
            f"Parser: Ollama Gemma report ready ({report_path.name}); "
            f"host={os.getenv('OLLAMA_HOST', 'http://localhost:11434')} model={os.getenv('GEMMA_MODEL', 'gemma4:e4b')}."
        ),
    )
    return {"clean_data": report, "messages": [msg]}


def auditor_node(state: AgentState) -> dict[str, Any]:
    """Scrape live site (Firecrawl), compare to ``clean_data``, write ``site_gaps.json``."""
    from agents.auditor_agent import run_audit_and_save

    clean = state.get("clean_data") or {}
    city = (state.get("city") or "unknown").strip()
    raw = state.get("raw_data") or ""
    gap_path = run_audit_and_save(clean, city=city, raw_data=raw)
    gap_report: dict[str, Any] = json.loads(gap_path.read_text(encoding="utf-8"))

    msg = AIMessage(
        content=f"Auditor: gap report written to {gap_path.relative_to(_project_root())}.",
    )
    return {"gap_report": gap_report, "messages": [msg]}


def _writer_llm() -> ChatGoogleGenerativeAI:
    api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "Set GOOGLE_API_KEY or GEMINI_API_KEY in .env for the Gemini writer (see .env.template)."
        )
    # Default avoids Gemini 3.x preview on free tier (often quota limit: 0 per API error).
    model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    return ChatGoogleGenerativeAI(model=model, api_key=api_key)


def _gemini_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def writer_node(state: AgentState) -> dict[str, Any]:
    """Draft semantic HTML5 service pages with Gemini (default ``gemini-2.5-flash``; override ``GEMINI_MODEL``)."""
    city = (state.get("city") or "your service area").strip()
    clean = state.get("clean_data") or {}
    result = clean.get("result") if isinstance(clean.get("result"), dict) else clean
    research_context = json.dumps(result, ensure_ascii=False, indent=2)[:12_000]

    gap = state.get("gap_report") or {}
    gap_block = (
        json.dumps(gap, ensure_ascii=False, indent=2)[:8000]
        if gap
        else "{}"
    )
    brand_identity = _load_brand_identity()
    brand_context = json.dumps(brand_identity, ensure_ascii=False, indent=2)
    phone = str(brand_identity.get("phone", "561-305-5853"))
    license_number = str(brand_identity.get("license_number", "CGC1519508"))

    system = SystemMessage(
        content=(
            "You are the D&B SEO Writer. You are an expert local SEO web copywriter for D&B Garage Doors, "
            "a garage door repair and installation company serving Palm Beach County, FL. "
            f"You MUST use the phone number {phone} and License #{license_number} in every footer and CTA. "
            "Do not hallucinate other numbers. "
            "Business details — Company: D&B Garage Doors | "
            f"Phone: {phone} | Email: service@dbgaragedoors.com | Website: dandbgaragedoors.com. "
            "ALWAYS use these exact details. NEVER use placeholders like [Your Company Name] or XXX-XXXX. "
            "Output only valid HTML (no markdown fences). "
            "Use semantic HTML5: header, nav, main, section, article, footer, address. "
            "Create a garage door repair service page for the given city: "
            "a compelling hero section, services (install, repair, spring, opener, cable, tune-up), "
            "emergency/24hr section, and contact/CTA with the real phone number and license. "
            "Include one clear h1 with the city and primary service. "
            "Write specific, local copy — mention real neighborhoods, landmarks, or characteristics of the city. "
            "Use the SITE_GAP_REPORT to close obvious gaps where appropriate."
        ),
    )
    user = HumanMessage(
        content=(
            f"City: {city}, FL. Generate the full multi-section HTML page for D & B Garage Doors.\n\n"
            f"BRAND_IDENTITY_JSON:\n{brand_context}\n\n"
            f"RESEARCH_JSON:\n{research_context}\n\n"
            f"SITE_GAP_REPORT (live site vs research):\n{gap_block}"
        ),
    )

    response = _writer_llm().invoke([system, user])
    draft = _gemini_content_to_text(response.content)

    msg = AIMessage(content=f"Writer: Gemini HTML draft ({len(draft)} chars).")
    return {"content_draft": draft, "messages": [msg]}


def hitl_notify_node(state: AgentState) -> dict[str, Any]:
    """Send Discord / email once (separate from ``interrupt`` so resume does not re-notify)."""
    from langgraph.config import get_config

    from agents.notifier import notify_human_review

    cfg = get_config()["configurable"]
    thread_id = str(cfg.get("thread_id", ""))
    notify_human_review(
        city=str(state.get("city") or ""),
        content_draft=str(state.get("content_draft") or ""),
        thread_id=thread_id,
        gap_report=state.get("gap_report") or {},
    )
    return {"messages": [AIMessage(content="HITL: notification sent (Discord/Resend if configured).")]}


def human_review_gate(state: AgentState) -> dict[str, Any]:
    """HITL: ``interrupt`` until resumed with ``Command(resume=...)``."""
    from langgraph.config import get_config

    cfg = get_config()["configurable"]
    thread_id = str(cfg.get("thread_id", ""))

    resume_payload = interrupt(
        {
            "type": "hitl_publish_review",
            "city": state.get("city"),
            "thread_id": thread_id,
            "instructions": (
                "Resume with Command(resume={'publish': True}) to run the publish worker, "
                "or Command(resume={'publish': False}) to skip."
            ),
            "draft_preview": (state.get("content_draft") or "")[:2500],
        }
    )

    approved = False
    if isinstance(resume_payload, dict):
        approved = bool(resume_payload.get("publish"))
    elif isinstance(resume_payload, bool):
        approved = resume_payload

    msg = AIMessage(
        content=("HITL: publish approved; running publisher." if approved else "HITL: publish skipped."),
    )
    return {"publish_approved": approved, "messages": [msg]}


def _html_to_markdown(html: str) -> str:
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", "", t)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|div|h[1-6]|li|tr|section|article)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def publisher_node(state: AgentState) -> dict[str, Any]:
    """POST Markdown draft to Cloudflare publish worker (Workers AI summarize) when approved."""
    if not state.get("publish_approved"):
        out = {"skipped": True, "reason": "publish_approved is false"}
        return {"publish_result": out, "messages": [AIMessage(content="Publisher: skipped (not approved).")]}

    worker_url = (os.getenv("PUBLISH_WORKER_URL") or "").strip().rstrip("/")
    token = (os.getenv("PUBLISH_AUTH_TOKEN") or os.getenv("AUTH_TOKEN") or "").strip()
    if not worker_url or not token:
        out = {
            "skipped": True,
            "reason": "Set PUBLISH_WORKER_URL and PUBLISH_AUTH_TOKEN (worker secret AUTH_TOKEN).",
        }
        return {"publish_result": out, "messages": [AIMessage(content="Publisher: missing worker URL or token.")]}

    html_draft = state.get("content_draft") or ""
    md = _html_to_markdown(html_draft)
    city = state.get("city") or ""

    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                f"{worker_url}/publish",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"markdown": md, "city": city},
            )
            r.raise_for_status()
            body = r.json()
    except Exception as exc:
        out = {"ok": False, "error": str(exc)}
        return {"publish_result": out, "messages": [AIMessage(content=f"Publisher: error {exc!r}.")]}

    deploy = body.get("deploy", {}) if isinstance(body, dict) else {}
    deploy_ok = deploy.get("ok") is True

    if deploy_ok:
        site_dir = (os.getenv("SITE_DIR") or "").strip()
        if site_dir and os.path.isdir(site_dir):
            import subprocess
            subprocess.run(["git", "stash"], cwd=site_dir, capture_output=True, text=True)
            pull = subprocess.run(["git", "pull", "--rebase"], cwd=site_dir, capture_output=True, text=True)
            subprocess.run(["git", "stash", "pop"], cwd=site_dir, capture_output=True, text=True)
            build = subprocess.run(
                ["npx", "wrangler", "pages", "deploy", ".", "--project-name", "db-garage-doors", "--commit-dirty=true"],
                cwd=site_dir, capture_output=True, text=True
            )
            deploy_log = {"pull": pull.stdout + pull.stderr, "deploy": build.stdout + build.stderr, "returncode": build.returncode}
            body = {**(body if isinstance(body, dict) else {}), "local_deploy": deploy_log}
            status = "deployed to Pages" if build.returncode == 0 else f"deploy failed (rc={build.returncode})"
        else:
            status = "worker committed to GitHub (set SITE_DIR to auto-deploy)"
    else:
        status = "worker error — not deployed"

    msg = AIMessage(content=f"Publisher: {status}.")
    return {"publish_result": body if isinstance(body, dict) else {"raw": body}, "messages": [msg]}


def _route_after_hitl(state: AgentState) -> Literal["publish", "skip"]:
    if state.get("publish_approved") is True:
        return "publish"
    return "skip"


def build_seo_graph() -> StateGraph:
    """researcher → parser → auditor → writer → HITL → (optional) publisher."""
    graph = StateGraph(AgentState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("gemma_parser", gemma_parser_node)
    graph.add_node("auditor", auditor_node)
    graph.add_node("writer", writer_node)
    graph.add_node("hitl_notify", hitl_notify_node)
    graph.add_node("human_review_gate", human_review_gate)
    graph.add_node("publisher", publisher_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "gemma_parser")
    graph.add_edge("gemma_parser", "auditor")
    graph.add_edge("auditor", "writer")
    graph.add_edge("writer", "hitl_notify")
    graph.add_edge("hitl_notify", "human_review_gate")
    graph.add_conditional_edges(
        "human_review_gate",
        _route_after_hitl,
        {"publish": "publisher", "skip": END},
    )
    graph.add_edge("publisher", END)
    return graph


def compile_seo_app(*, checkpointer: Any | None = None, **compile_kwargs: Any):
    """Compile graph with a checkpointer (required for ``interrupt`` / HITL).

    Defaults to SQLite at ``data/checkpoints.sqlite`` so a separate process can resume
    (see ``resume_hitl.py``). Set ``LANGGRAPH_MEMORY_CHECKPOINTER=1`` for in-memory only.
    """
    if checkpointer is not None:
        return build_seo_graph().compile(checkpointer=checkpointer, **compile_kwargs)

    if os.getenv("LANGGRAPH_MEMORY_CHECKPOINTER", "").lower() in ("1", "true", "yes"):
        from langgraph.checkpoint.memory import MemorySaver

        return build_seo_graph().compile(checkpointer=MemorySaver(), **compile_kwargs)

    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    db_path = _project_root() / "data" / "checkpoints.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return build_seo_graph().compile(checkpointer=SqliteSaver(conn), **compile_kwargs)
