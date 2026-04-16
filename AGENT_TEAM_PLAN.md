# SEO Agent Team Plan

## Core Goal
Build an AI-assisted SEO execution system that helps you research, create, and optimize search content faster while keeping output quality consistent and measurable.

## What You Plan To Use
- **Backend**: Flask (Python) for APIs, orchestration, and agent task routing.
- **Frontend**: Next.js 16.2 for dashboards, task queues, and content review UX.
- **SEO Framework**: Semantic HTML5 content structure and keyword targeting (aiming for ~1.2% density where appropriate).
- **Scraping**: Firecrawl MCP for external page/article extraction.
- **Data Storage Pattern**:
  - Raw scraped data -> `/data/raw/`
  - Cleaned/processed data -> `/data/clean/`

## Agent Team Responsibilities
- **Research Agent**
  - Finds SERP competitors, headings, entities, and topic gaps.
  - Pulls source pages via Firecrawl MCP.
- **Cross-Reference / Auditor Agent** (`agents/auditor_agent.py`)
  - Scrapes the live site (default `https://www.dandbgaragedoors.com/`) via Firecrawl `/v1/scrape`.
  - Compares H1, meta descriptions, and city/service signals against `clean_data` from research.
  - Writes `/data/clean/site_gaps.json` (gap report vs competitors / research text).
- **Content Agent**
  - Drafts outlines and SEO-first content based on research packets.
  - Produces semantic HTML-ready sections.
- **On-Page Agent**
  - Optimizes title tags, meta descriptions, headings, schema hints, and internal linking suggestions.
- **QA Agent**
  - Verifies factual consistency, keyword usage, readability, and structure.
  - Flags thin content and missing sections before publish.
- **Publishing/Workflow Agent**
  - Moves approved output through your Flask/Next.js workflow.
  - Tracks status from "researched" -> "drafted" -> "reviewed" -> "published".
- **Human-in-the-Loop (HITL)** (`agents/notifier.py` + `human_review_gate` in LangGraph)
  - After the writer, execution pauses on an `interrupt` until you resume with `Command(resume={"publish": True|False})`.
  - Optional Discord webhook and/or Resend email with the `thread_id` and `resume_hitl.py` commands.
- **Cloudflare publish worker** (`backend/publish_worker.ts`)
  - Authorized POST with Markdown; Workers AI (Llama 3.1) summarizes before you wire Pages deploy.

## End-to-End Workflow
1. **Input**: Seed keyword, target page, or content brief (e.g. city for local garage door pages).
2. **Collect**: Firecrawl MCP gathers source pages.
3. **Normalize**: Save raw and cleaned datasets to the required folders.
4. **Audit**: Cross-reference live site vs research → `site_gaps.json`.
5. **Generate**: Draft content (writer uses gap report + research).
6. **HITL**: Notify and pause for human approve/reject before any publish call.
7. **Publish** (if approved): POST Markdown to the Cloudflare Worker (Workers AI summarize; wire Pages deploy next).
8. **Iterate**: Track performance and feed learnings into next runs.

## Success Metrics You Can Track
- Organic traffic growth by page/topic cluster.
- Ranking movement for primary and secondary keywords.
- CTR changes from title/meta improvements.
- Time-to-publish reduction per content piece.
- Acceptance rate of first-pass AI drafts after human review.

## Guiding Constraints
- Keep content useful first, optimized second.
- Use semantic HTML5 consistently.
- Follow the project rule for keyword density targets without forcing unnatural phrasing.
- Keep a clear audit trail between raw scraped evidence and final published claims.

## Quick Operating Checklist
- [ ] Define target keyword + intent
- [ ] Scrape sources with Firecrawl MCP
- [ ] Save raw data to `/data/raw/`
- [x] Save cleaned data to `/data/clean/`
- [ ] Generate draft + on-page metadata
- [ ] Run QA checks
- [ ] Human review/approval
- [ ] Publish and monitor results
- [x] Automation Rules Established.
- [x] Cross-Reference Auditor + HITL gate + publish worker scaffolding (see `agents/auditor_agent.py`, `agents/notifier.py`, `backend/publish_worker.ts`).
