# SEO Agent Team - Current Build Handoff

This repository now contains an autonomous SEO factory scaffold with research, parsing, auditing, writing, human approval, and publish wiring.

## Implemented Components

- `agents/orchestrator.py`
  - LangGraph state flow:
    - `researcher` -> `gemma_parser` -> `auditor` -> `writer` -> `hitl_notify` -> `human_review_gate` -> (`publisher` or end)
  - Firecrawl research ingestion (`/v1/search`) saves raw JSON to `data/raw`.
  - Gemma parser node delegates to `agents/gemma_processor.py` (Ollama/Gemma 4).
  - Auditor node generates site gap analysis before writing.
  - Writer node uses LangChain Google GenAI to produce HTML.
  - HITL gate uses `langgraph.types.interrupt()` and resumes with `Command(resume={"publish": True|False})`.
  - Publisher node calls Cloudflare Worker when approved.
  - SQLite checkpointing enabled by default at `data/checkpoints.sqlite`.

- `agents/gemma_processor.py`
  - Uses `ollama` Python library.
  - Defaults to `OLLAMA_HOST=http://localhost:11434`.
  - Defaults to `GEMMA_MODEL=gemma4:e4b`.
  - Cleans raw SEO source payloads and writes clean reports to `data/clean`.

- `agents/auditor_agent.py`
  - Scrapes live site with Firecrawl (`/v1/scrape`).
  - Compares live H1/meta/city/service signals vs research `clean_data`.
  - Writes `data/clean/site_gaps.json`.

- `agents/notifier.py`
  - Sends human review notifications via:
    - Discord webhook (`DISCORD_WEBHOOK_URL`)
    - Resend email (`RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `HITL_NOTIFY_EMAIL`)

- `backend/publish_worker.ts`
  - Cloudflare Worker requiring `Authorization: Bearer <AUTH_TOKEN>`.
  - Accepts Markdown via POST `/publish`.
  - Summarizes content using Workers AI Llama 3.1.
  - Returns publish payload/summary scaffolding response.

- `backend/wrangler.toml`
  - Worker config and AI binding.

- `run_seo_pipeline.py`
  - Loads `.env`.
  - Runs pipeline for `{"city": "Boca Raton"}`.
  - Handles HITL interruption and optional auto-approve.
  - Prints and saves final HTML to `data/clean`.

- `resume_hitl.py`
  - Resumes paused LangGraph runs by `thread_id`.
  - Usage: `python resume_hitl.py <THREAD_ID> approve|reject`.

## Key Environment Variables

- Firecrawl:
  - `FIRECRAWL_API_KEY`
  - `FIRECRAWL_BASE_URL`
- Gemini writer:
  - `GOOGLE_API_KEY` or `GEMINI_API_KEY`
  - `GEMINI_MODEL` (default currently set to free-tier-friendly option)
- Gemma parser:
  - `OLLAMA_HOST`
  - `GEMMA_MODEL=gemma4:e4b`
- HITL notifications:
  - `DISCORD_WEBHOOK_URL`
  - `HITL_NOTIFY_EMAIL`
  - `RESEND_API_KEY`
  - `RESEND_FROM_EMAIL`
- Publishing:
  - `PUBLISH_WORKER_URL`
  - `PUBLISH_AUTH_TOKEN`
- Pipeline behavior:
  - `AUTO_APPROVE_HITL`
  - `LANGGRAPH_MEMORY_CHECKPOINTER`

## Operational Notes

- `.env` is gitignored and should never be committed.
- If using manual HITL, set `AUTO_APPROVE_HITL=false`.
- Cloudflare Worker deploy still needs your own page update hook (GitHub commit, Pages API, or storage pipeline) after summary.

## Typical Run Commands

- Install dependencies:
  - `pip install -r requirements.txt`
- Run pipeline (once):
  - `venv/bin/python run_seo_pipeline.py`
- Resume HITL:
  - `python resume_hitl.py <THREAD_ID> approve`

### PM2 Scheduling (Hourly)

- **Check status:** `pm2 status`
- **Stop schedule:** `pm2 stop db-seo-factory`
- **Start/Resume schedule:** `pm2 start venv/bin/python --name "db-seo-factory" -- run_seo_pipeline.py --cron "0 * * * *"`
- **Save current state:** `pm2 save`
- **View logs:** `pm2 logs db-seo-factory`

