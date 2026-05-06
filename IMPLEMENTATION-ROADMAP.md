# Implementation Roadmap — Garage Door SEO
**Site:** dandbgaragedoors.com  
**Duration:** 6 months (April – September 2026)  
**Starting Score:** 30/100 → Target: 78/100

---

## Phase Overview

| Phase | Weeks | Focus | Pages Added | Target Score |
|-------|-------|-------|-------------|-------------|
| **Phase 1: Foundation** | 1-4 | Technical fixes, core pages, GBP | +12 pages | 50/100 |
| **Phase 2: Expansion** | 5-12 | City pages, blog velocity, reviews | +18 pages | 65/100 |
| **Phase 3: Scale** | 13-20 | Blog depth, link building, GEO | +12 pages | 72/100 |
| **Phase 4: Authority** | 21-24 | Optimization, refresh, compound | +8 pages | 78/100 |

---

## Phase 1: Foundation (Weeks 1-4, April 2026)

### Objective
Eliminate critical blockers. Make the site technically sound. Publish core pages. Launch GBP. Start review acquisition.

### Week 1: Technical Sprint (Est. 4-6 hours)

**Developer tasks:**
- [ ] Fix `<link rel="canonical" href="./">` → `href="https://dandbgaragedoors.com/"`
- [ ] Fix schema `"url": "./"` → `"url": "https://dandbgaragedoors.com/"`
- [ ] Remove D1 debug message from HTML
- [ ] Fix unrendered JS template in H3 heading
- [ ] Add Cloudflare redirect rule: HTTP → HTTPS (301)
- [ ] Add security headers via Cloudflare Transform Rules:
  ```
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  ```
- [ ] Allow `Google-Extended`, `GPTBot`, `PerplexityBot` in robots.txt
- [ ] Create `sitemap.xml` with homepage URL + declare in robots.txt
- [ ] Add Open Graph + Twitter Card meta tags to `<head>`
- [ ] Add favicon (`/favicon.png` + `<link rel="icon">`)
- [ ] Create `llms.txt` at root

**Estimated impact:** SEO Health Score +8-10 points

---

### Week 2: Core Pages

**Content to publish:**

1. **About Page** (`/about/`) — 700 words
   - Founding story, years in business, Florida license #, insurance, team photo
   - Schema: `LocalBusiness` + `Person` (founder)

2. **Emergency Page** (`/emergency/`) — 500 words
   - Above-fold: phone number, "available now" signal, response time
   - Sections: What counts as an emergency, our response process, service area
   - Schema: `Service`

3. **Contact Page** (`/contact/`) — 300 words
   - Phone, email, service area map, contact form
   - Schema: `ContactPage`

4. **Updated Homepage** (`/`) — 1,000+ words
   - New H1: "Garage Door Repair & Installation — Palm Beach County, FL"
   - Full expanded schema (from FULL-AUDIT-REPORT.md Section 4)
   - Sections: Hero, Services grid (with links), Service area, Trust signals, CTA

---

### Week 3: Service Page Build-Out

5. **Spring Repair** (`/services/garage-door-spring-repair/`) — 1,000 words
6. **Opener Repair** (`/services/garage-door-opener-repair/`) — 900 words
7. **Installation** (`/services/garage-door-installation/`) — 1,000 words
8. **Boca Raton** (`/locations/boca-raton/`) — 650 words
9. **West Palm Beach** (`/locations/west-palm-beach/`) — 650 words

---

### Week 4: Remaining Services + Blog Launch + Citations

10. **Cable Repair** (`/services/garage-door-cable-repair/`) — 800 words
11. **Tune-Up** (`/services/garage-door-tune-up/`) — 800 words
12. **Replacement** (`/services/garage-door-replacement/`) — 800 words
13. **Blog Post 1:** Cost guide — 1,200 words

**Citation submissions:**
- [ ] Google Business Profile (video verification ready)
- [ ] Bing Places for Business
- [ ] Apple Maps
- [ ] Yelp (Garage Door Services category)
- [ ] Facebook Business Page

**Review launch:**
- [ ] Send review request emails to existing customers
- [ ] Set up post-service SMS workflow
- [ ] Generate short review link from GBP dashboard

**Phase 1 Deliverable Summary:**
- 12 new pages published
- Technical score fixed
- GBP live with 8 cities configured
- First 5 citations submitted
- 5-8 reviews acquired

---

## Phase 2: Expansion (Weeks 5-12, May-June 2026)

### Objective
Complete all city pages. Build blog velocity. Hit 20+ reviews. Begin seeing first ranking signals.

### Weeks 5-8: City Pages + Blog (May)

**Pages to publish:**
- Delray Beach, Boynton Beach, Wellington, Jupiter, Palm Beach Gardens, Lake Worth, Greenacres, Royal Palm Beach (8 city pages)
- FAQ Page (`/faq/`) — 1,800 words
- Blog posts 2-4 (see CONTENT-CALENDAR.md)

**Citation submissions:**
- [ ] HomeAdvisor
- [ ] Angi (Angie's List)
- [ ] BBB (Better Business Bureau)
- [ ] Thumbtack
- [ ] Nextdoor Business

**GBP activities:**
- Weekly posts (service tips, seasonal, customer stories)
- Upload 10+ photos (before/after, team, equipment, garage doors)
- Ensure all services listed in GBP service catalog
- Respond to all reviews within 24 hours

### Weeks 9-12: Depth + Reviews Milestone (June)

**Pages to publish:**
- Reviews/Testimonials page (`/reviews/`) — 400 words + embeds
- Gallery (`/gallery/`) — 300 words + photos
- Blog posts 5-8

**Review target:** 20+ by end of June  
**GBP photos target:** 20+ photos (Google prioritizes profiles with more photos)

**Link building begins:**
- Reach out to 3-5 Palm Beach County home improvement / real estate blogs
- Submit to IDA (International Door Association) member directory
- Sponsor or participate in local community event (Nextdoor, local Facebook groups)

**Phase 2 Deliverable Summary:**
- All 8 city pages live
- 8 blog posts published
- 20+ Google reviews
- 15+ citations
- First keyword rankings appearing in GSC

---

## Phase 3: Scale (Weeks 13-20, July-August 2026)

### Objective
Build blog authority. Deepen content on top performers. Begin compound SEO growth.

### Weeks 13-16: Blog Authority (July)

- Blog posts 9-12 (seasonal + problem-diagnosis cluster)
- Internal link audit: ensure all city pages link to service pages and vice versa
- Add Article schema to all blog posts
- GBP: Hurricane season content, emergency service posts

### Weeks 17-20: Content Optimization (August)

- Blog posts 13-16
- Identify top-performing pages in GSC — expand word count by 200-400 words
- Add FAQ sections to underperforming city pages
- Add `AggregateRating` schema to homepage once 20+ reviews confirmed
- Set up Google Search Console alerts for position drops

**Schema expansion target:**
- Service schema on all 6 service pages
- `LocalBusiness` with `geo` on all 8 city pages
- `Article` on all blog posts
- `AggregateRating` on homepage

**Phase 3 Deliverable Summary:**
- 24 total blog posts
- 50+ indexed pages
- 30+ reviews
- Schema on all key pages
- Tracking rankings for 50+ keywords

---

## Phase 4: Authority (Weeks 21-24, September 2026)

### Objective
Consolidate gains. Refresh content. Prepare for Year 2.

### Weeks 21-22: Refresh + Audit

- Run `/seo audit dandbgaragedoors.com` for 6-month score comparison
- Identify which city pages are ranking for their target keywords
- Expand top-3 performing city pages with 200-400 additional words
- Refresh Blog Post 1 (cost guide) with updated 2026 pricing

### Weeks 23-24: Year 2 Prep

- Blog posts 21-24
- Evaluate programmatic SEO for service+city combos (e.g., "spring repair boca raton" as a dedicated page vs. blog post)
- Competitor gap analysis: identify keywords competitors rank for that D&B doesn't
- Plan Year 2 priorities based on GSC data

**Phase 4 Deliverable Summary:**
- 24 total blog posts published
- Site refreshed and audited
- 35-40 reviews
- Year 2 roadmap drafted

---

## Resource Requirements

### Time Investment (Owner/Small Team)

| Task | Hours/Month | Who |
|------|-------------|-----|
| Technical fixes (Phase 1 only) | 6 hrs | Developer |
| Content writing (pages + blog) | 15-20 hrs | Owner or writer |
| GBP management (posts, photos, reviews) | 4 hrs | Owner |
| Citation submissions | 3 hrs (Month 1-2 only) | Owner |
| Link building outreach | 3-4 hrs | Owner |
| Analytics review | 1 hr | Owner |
| **Total/month (ongoing)** | **~25 hrs** | |

### Cost Estimates (If Outsourcing)

| Item | Est. Cost |
|------|-----------|
| Technical fixes (one-time) | $200-500 |
| Content writing (per page, 800-1,000 words) | $75-150/page |
| Blog post writing (1,200 words) | $100-200/post |
| GBP management | $100-200/month |
| Citation building service | $100-200 one-time |
| **Total 6 months (outsourced)** | **$3,000-6,500** |

**Expected return:** At industry conversion rates of 2-3%, 400 monthly organic visits = 8-12 new customers/month. Average garage door job = $300-800. Monthly revenue from SEO: **$2,400-9,600/month** by Month 6.

---

## Key Milestones & Check-ins

| Date | Milestone | Check |
|------|-----------|-------|
| Apr 14 | All technical fixes deployed | Re-run `/seo technical dandbgaragedoors.com` |
| Apr 30 | GBP live, 8 core pages published | Check GSC for indexation |
| May 31 | All 8 city pages live, 5 blog posts published | First ranking signals in GSC |
| Jun 15 | 20+ Google reviews | GBP rank check for Boca Raton + WPB |
| Jul 31 | 15 blog posts, 30+ reviews | Keyword ranking report |
| Sep 30 | Full 6-month audit | `/seo audit dandbgaragedoors.com` |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GBP suspended (new profile) | Medium | High | Use video verification, accurate info, no keyword stuffing in name |
| Content quality issues (thin) | Medium | High | Use content templates, minimum word counts, unique local angle |
| Review spam / negative review | Low | Medium | Respond professionally within 6 hours, flag spam reviews |
| Competitor copies city pages | Low | Low | Add unique local photos, specific neighborhood details |
| Algorithm update (core update) | Low | Medium | Focus on E-E-A-T, never keyword stuffing — Google-safe approach |
| Blog system remains broken | Medium | High | Fallback: use static pages at `/blog/[slug]/` — bypass D1 entirely |

---

## Tracking Setup Checklist

- [ ] Google Search Console (verify dandbgaragedoors.com)
- [ ] Google Analytics 4 (add GA4 tracking to site)
- [ ] Configure GSC + GA4 integration
- [ ] Set up conversion tracking: phone clicks, form submits
- [ ] GBP Insights (built-in: views, calls, direction requests)
- [ ] Monthly rank tracking spreadsheet (or tool like BrightLocal)
- [ ] Set up Google Alerts for "D & B Garage Doors" + "garage door repair Palm Beach"
