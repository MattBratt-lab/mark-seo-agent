# SEO agent team — project handoff

**Repo:** `c:\projects\seo-scraper-bot`  
**Primary domain:** https://www.dandbgaragedoors.com  
**Handoff date:** 2026-04-14  

This file is the **single entry point** for anyone (human or agent) picking up SEO, content, deploy, or research work on this site.

**Copy layout (this `SEO_Agent_Team` folder):** Status docs, Firecrawl JSON, and `agents/*.md` live at this level. Deploy scripts, `package.json`, and Pages Functions are mirrored under [`seo-scraper-site-reference/`](../seo-scraper-site-reference/) (copied from `c:\projects\seo-scraper-bot`). **Site HTML** (`index.html`, `locations/`, `services/`, etc.) was not duplicated here; keep editing those files in the `seo-scraper-bot` repo.

---

## 1) Canonical status and roadmap

Read first:

| Document | Purpose |
|----------|---------|
| [`WEBSITE-STATUS-AND-PLAN.md`](../WEBSITE-STATUS-AND-PLAN.md) | Current site state, NAP, structure, gaps, prioritized next steps |

Other useful repo docs (optional context):

- [`SEO-STRATEGY.md`](../SEO-STRATEGY.md), [`SITE-STRUCTURE.md`](../SITE-STRUCTURE.md), [`CONTENT-CALENDAR.md`](../CONTENT-CALENDAR.md)
- [`CLAUDE.md`](../CLAUDE.md) — Claude SEO skill ecosystem, commands, security rules for scripts

---

## 2) Firecrawl research outputs (Boca Raton)

| File | Purpose |
|------|---------|
| [`.firecrawl/research-boca-raton.json`](../.firecrawl/research-boca-raton.json) | Raw Firecrawl search+scrape JSON (single line) |
| [`.firecrawl/research-boca-raton.pretty.json`](../.firecrawl/research-boca-raton.pretty.json) | Same data, formatted for reading |
| [`.firecrawl/install-check.md`](../.firecrawl/install-check.md) | Post-install smoke scrape note |

**Security:** A Firecrawl API key was shared in chat during setup. **Rotate the key** in the Firecrawl dashboard if there is any doubt it was exposed, then re-run `npx -y firecrawl-cli@latest init` locally as needed.

---

## 3) Source vs build output

| Area | Path |
|------|------|
| Editable HTML, CSS source | Root: `index.html`, `about/`, `blog/`, `contact/`, `faq/`, `privacy/`, `locations/`, `services/`, `css/input.css` |
| Generated CSS | `css/style.css` (from `npm run build:css`) |
| **Deploy artifact** | `dist/` — produced by `npm run build` (do not hand-edit `dist/` as source of truth) |
| Static sync | [`scripts/sync-dist.mjs`](../seo-scraper-site-reference/scripts/sync-dist.mjs) copies listed files/dirs + `images/` into `dist/` and regenerates valid path lists for middleware |

---

## 4) Cloudflare Pages — functions and deploy

**Pages Functions** (edge logic next to static deploy):

- [`functions/_middleware.ts`](../seo-scraper-site-reference/functions/_middleware.ts) — routing, real 404s for invalid paths
- [`functions/_valid-paths.ts`](../seo-scraper-site-reference/functions/_valid-paths.ts) — generated valid pathname set (build output)
- [`functions/_404-html.ts`](../seo-scraper-site-reference/functions/_404-html.ts) — 404 HTML fragment
- [`functions/get-blogs.ts`](../seo-scraper-site-reference/functions/get-blogs.ts) — blog API route

**Deploy command (repo default):**

```bash
npm run deploy:pages
```

This runs `build`, then `wrangler pages deploy dist --branch main --commit-dirty=true`, then [`scripts/deploy-note.mjs`](../seo-scraper-site-reference/scripts/deploy-note.mjs).

**Action for the team:** Confirm in the Cloudflare Pages project which Git **production branch** is actually wired (`main` vs `master`). The status doc flags past confusion; align the dashboard, local habits, and `package.json` so only one branch is production.

**Local preview:**

```bash
npm run dev:pages
```

**Verify functions bundle:**

```bash
npm run verify:functions
```

---

## 5) Separate Worker (optional / blog bot)

| Path | Notes |
|------|------|
| [`cloudfare_worker/index.ts`](../seo-scraper-site-reference/cloudfare_worker/index.ts) | Worker entry (copy of `src/index.ts` from site repo) |
| [`cloudfare_worker/wrangler.jsonc`](../seo-scraper-site-reference/cloudfare_worker/wrangler.jsonc) | Worker name `garage-blog-bot`, D1 binding `garage-db` |

Deploy:

```bash
npm run deploy:worker
```

Comments in `wrangler.jsonc` note that `/get-blogs` is intended to be served by **Pages** `functions/`, not zone-routed through this Worker.

---

## 6) Form / email (Resend)

From [`WEBSITE-STATUS-AND-PLAN.md`](../WEBSITE-STATUS-AND-PLAN.md):

- Worker-style flow uses **`RESEND_API_KEY`**
- Pages secret: `npx wrangler pages secret put RESEND_API_KEY`
- Documented sender/recipient: `website@dbgaragedoors.us` → `anthony@dbgaragedoors.us`

Confirm the live `/submit` (or equivalent) path and test end-to-end after any infra change.

---

## 7) NPM scripts the SEO / ops team cares about

Run these from **`c:\projects\seo-scraper-bot`** (or copy `seo-scraper-site-reference/package.json` + `scripts/` + `functions/` back beside each other if you need a standalone tree).

| Script | Command |
|--------|---------|
| Full static build | `npm run build` |
| CSS only | `npm run build:css` |
| Live smoke checks | `npm run check:live` |
| External audit helper | `npm run audit:live` |
| Robots / AI crawlers check | `npm run verify:robots` |
| D1 local migrate | `npm run d1:migrate:local` |
| D1 remote migrate / seed | `npm run d1:migrate:remote` / `npm run d1:seed:remote` |

---

## 8) Agent definitions (this folder)

Subagent markdown lives under [`agents/`](../agents/) (e.g. `seo-local.md`, `seo-technical.md`). These align with the broader **Claude SEO** layout described in [`CLAUDE.md`](../CLAUDE.md).

---

## 9) Suggested follow-ups for the agent team

1. **Branch:** Lock production to one branch; document it here once confirmed.
2. **Keys:** Rotate Firecrawl key if exposed; keep Resend only in Wrangler secrets.
3. **SEO:** Reconcile Firecrawl research with `c:\projects\seo-scraper-bot\locations\boca-raton\index.html` (not copied here) — gaps, headings, FAQs, internal links.
4. **Analytics:** Status doc — GTM + GA4 + GSC verification still planned.
5. **Repeat research:** Run additional Firecrawl searches (competitors, “near me” variants) and save under `.firecrawl/` with descriptive names.

---

## 10) Quick “files to open” checklist

1. `WEBSITE-STATUS-AND-PLAN.md` (this folder)  
2. `.firecrawl/research-boca-raton.pretty.json` (this folder)  
3. `seo-scraper-site-reference/package.json`  
4. `seo-scraper-site-reference/functions/_middleware.ts`  
5. `seo-scraper-site-reference/scripts/sync-dist.mjs`  
6. Homepage + priority location (site repo only): `c:\projects\seo-scraper-bot\index.html`, `...\locations\boca-raton\index.html`

---

*End of handoff. Update this file when production branch, form endpoint, or major SEO decisions change.*
