# D&B Garage Doors Website — Current State + Plan
**Date:** 2026-04-14  
**Owner:** D&B Garage Doors  
**Primary Domain:** https://www.dandbgaragedoors.com

---

## 1) Current State (What the site has right now)

## Platform / Deployment
- Hosted on **Cloudflare Pages**
- Build is static HTML/CSS/JS with Pages Functions
- Primary deploy flow used in repo: `npm run deploy:pages`
- Branch mapping has caused confusion before (`main` vs `master`), so production branch targeting should be standardized

## Core Site Structure
- Main pages:
  - `/`
  - `/about/`
  - `/contact/`
  - `/faq/`
  - `/privacy/`
  - `/blog/`
- Service pages:
  - `/services/garage-door-spring-repair/`
  - `/services/garage-door-opener-repair/`
  - `/services/garage-door-installation/`
  - `/services/garage-door-cable-repair/`
  - `/services/garage-door-tune-up/`
  - `/services/garage-door-replacement/`
  - `/services/emergency-garage-door-repair/`
- Location pages:
  - `/locations/boca-raton/`
  - `/locations/west-palm-beach/`
  - `/locations/delray-beach/`
  - `/locations/boynton-beach/`
  - `/locations/wellington/`
  - `/locations/jupiter/`
  - `/locations/palm-beach-gardens/`
  - `/locations/lake-worth/`

## Contact / NAP (current)
- Phone: **(561) 305-0877**
- Email: **anthony@dbgaragedoors.us**
- Address used: **9323 Talway Circle, Boynton Beach, FL 33472**
- Click-to-call links and contact email are present

## Homepage Content (current)
- Hero section + CTA present
- “Our Work Across Palm Beach County” photo/gallery section present
- “Client Voices” testimonials/reviews section present

## SEO / Technical (current)
- JSON-LD exists on homepage and many internal pages
- `robots.txt`, `sitemap.xml`, and `llms.txt` exist
- Pages middleware exists to return real 404 for invalid routes
- Redirects file exists and includes emergency-page redirects and blog slug redirect handling

## Marketing/Tracking Scripts (current)
- No GTM / GA4 / Meta Pixel / Search Console verification tags found in source scan

## Form + Email Pipeline (current)
- Cloudflare Worker endpoint logic exists for `/submit`
- Worker uses Resend with secret key from env:
  - `env.RESEND_API_KEY`
- Current sender/recipient in worker:
  - From: `website@dbgaragedoors.us`
  - To: `anthony@dbgaragedoors.us`
- Secret command for Pages:
  - `npx wrangler pages secret put RESEND_API_KEY`

---

## 2) What we plan to do next

## Priority A — Stabilize Deployment + Rollout
- [ ] Lock production to one branch (recommend `main` or `master`, not both)
- [ ] Update deploy script to target only production branch
- [ ] Add post-deploy smoke check script:
  - homepage 200
  - logo 200
  - contact email/phone string checks
  - schema parse check

## Priority B — Contact Funnel Finalization
- [ ] Confirm form submits to final endpoint (`/submit` same-domain vs worker subdomain)
- [ ] Add success/failure logging and anti-spam guard (basic rate limit/CAPTCHA)
- [ ] Test full lead flow:
  - submit form
  - email arrives at `anthony@dbgaragedoors.us`
  - include all fields (Name, Phone, Address, ServiceType)

## Priority C — SEO Hardening
- [ ] Keep canonical/NAP/schema consistent across all pages
- [ ] Re-run rich results validation after every schema edit
- [ ] Add/verify FAQPage blocks where intended
- [ ] Expand thin location/service pages to target word-count + local relevance

## Priority D — Marketing Analytics
- [ ] Add GTM container
- [ ] Add GA4 via GTM (not hardcoded directly)
- [ ] Add Meta Pixel via GTM if required
- [ ] Add Search Console verification meta/file

## Priority E — Content + UX
- [ ] Finalize homepage visual style direction and lock it (to avoid rollback churn)
- [ ] Keep gallery/review sections while refining typography and spacing
- [ ] Verify mobile tap targets + contrast + performance

---

## 3) Immediate Next Actions (today)
1. Confirm production branch mapping in Cloudflare Pages.
2. Confirm final form endpoint route and run end-to-end test.
3. Add GTM + GA4 baseline.
4. Freeze homepage layout/version and avoid mid-cycle reversions.
5. Run one fresh external audit and capture baseline score.

---

## 4) Notes
- Goal going forward: **single source of truth** for production branch + repeatable deploy + measurable analytics.
