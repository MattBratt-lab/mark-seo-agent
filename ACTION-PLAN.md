# Action Plan — D & B Garage Doors SEO
**Site:** https://dandbgaragedoors.com/  
**Generated:** 2026-04-01  
**SEO Health Score:** 30/100 → Target: 70/100 in 90 days

---

## 🔴 CRITICAL — Do Today (< 1 hour total)

### C1. Fix canonical tag (5 min)
**File:** `index.html` (or wherever `<head>` is managed)
```html
<!-- Change this -->
<link rel="canonical" href="./" />

<!-- To this -->
<link rel="canonical" href="https://dandbgaragedoors.com/" />
```

### C2. Remove debug message from HTML (5 min)
**Find and remove:**
> "If nothing shows, confirm your D1 table `posts` includes columns like `title`, `content`, `date`, and `city`."

This is visible to Google and all visitors — remove or move to a comment.

### C3. Fix schema `url` field (2 min)
```json
// Change:
"url": "./"

// To:
"url": "https://dandbgaragedoors.com/"
```

### C4. Add HTTP → HTTPS redirect (10 min)
In Cloudflare Dashboard → Rules → Redirect Rules → Create rule:
- When: Scheme equals `http`
- Then: Redirect to `https://${host}${uri}` (301)

### C5. Fix broken JS template in H3 (variable time)
The heading contains `' + escapeHtml(title) + '` as literal text in the HTML. Fix the Cloudflare Pages Function / Worker template that generates this.

---

## 🟠 HIGH PRIORITY — Week 1

### H1. Add sitemap.xml (1 hr)
Create `/sitemap.xml` with at minimum the homepage:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://dandbgaragedoors.com/</loc>
    <lastmod>2026-04-01</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

Add to robots.txt:
```
Sitemap: https://dandbgaragedoors.com/sitemap.xml
```

### H2. Open Graph + Twitter Cards (30 min)
Add to `<head>`:
```html
<!-- Open Graph -->
<meta property="og:title" content="D & B Garage Doors — Garage Door Repair Palm Beach County FL" />
<meta property="og:description" content="Fast, reliable garage door repair and installation in Palm Beach County, FL. Spring repair, opener repair, emergency service. Call (561) 305-5853." />
<meta property="og:url" content="https://dandbgaragedoors.com/" />
<meta property="og:type" content="website" />
<meta property="og:image" content="https://dandbgaragedoors.com/images/og-image.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="en_US" />
<meta property="og:site_name" content="D & B Garage Doors" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="D & B Garage Doors — Garage Door Repair Palm Beach County" />
<meta name="twitter:description" content="Fast garage door repair & installation in Palm Beach County, FL. Call (561) 305-5853." />
<meta name="twitter:image" content="https://dandbgaragedoors.com/images/og-image.jpg" />
```

### H3. Allow AI Overviews crawler (10 min)
In robots.txt, add before Cloudflare managed section:
```
User-agent: Google-Extended
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /
```

### H4. Expand Schema (1 hr)
Replace current schema with the full corrected version from the Full Audit Report (Section 4).

### H5. Create Google Business Profile
If not already done:
1. Go to business.google.com
2. Create profile for "D & B Garage Doors"
3. Category: "Garage door supplier" + "Garage door repair service"
4. Add phone, service area, hours, photos
5. Verify via postcard or phone
6. Add GBP URL to schema `sameAs` array

### H6. Add favicon (15 min)
```html
<link rel="icon" type="image/png" href="/favicon.png" sizes="32x32" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
```

### H7. Add security headers via Cloudflare (30 min)
Cloudflare → Rules → Transform Rules → Modify Response Header:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(self)
```

---

## 🟡 MEDIUM PRIORITY — Month 1

### M1. Fix or replace broken blog system
**Option A:** Fix Cloudflare D1 Worker — deploy the `/get-blogs` Pages Function properly  
**Option B:** Replace with static blog pages at `/blog/[slug]/`  
**Option C:** Integrate a headless CMS (Contentful, Sanity, Notion API)

Recommended: Build 2-3 static blog posts first to prove content value, then automate:
- "How to Know When Your Garage Door Springs Need Replacement"
- "Garage Door Maintenance Checklist for Florida Homeowners"
- "LiftMaster vs Chamberlain: Which Opener is Right for Palm Beach County Homes?"

### M2. Create About Page (/about/)
Must include:
- Company founding story and year
- Service area explanation
- Florida contractor license number (if applicable)
- Insurance/bonding statement
- Team photo (builds E-E-A-T)
- "Why choose us" bullet points with specific, verifiable claims

### M3. Create Service Pages (6 pages)
Each page needs:
- Unique 600+ word content
- Service-specific H1 (e.g., "Garage Door Spring Repair in Palm Beach County")
- LocalBusiness + Service schema
- CTA with phone number
- FAQ section (3-5 questions)
- Photo of the service being performed

Pages:
1. `/services/garage-door-spring-repair/`
2. `/services/garage-door-opener-repair/`
3. `/services/garage-door-installation/`
4. `/services/emergency-garage-door-repair/`
5. `/services/garage-door-cable-repair/`
6. `/services/garage-door-tune-up/`

### M4. Create City Landing Pages (8 pages)
Each page:
- City-specific H1: "Garage Door Repair in [City], FL"
- Mention local neighborhoods, landmarks
- Service list with city references
- Embedded Google Map of service area
- LocalBusiness schema with city in address
- Phone + CTA

Cities: Boca Raton, West Palm Beach, Delray Beach, Boynton Beach, Wellington, Jupiter, Palm Beach Gardens, Lake Worth

### M5. Add Reviews Section to Homepage
- Embed Google reviews widget
- Display 3-5 selected testimonials with name, city, star rating
- Add Review schema to page

### M6. Add llms.txt
Create at `https://dandbgaragedoors.com/llms.txt`:
```markdown
# D & B Garage Doors
> Professional garage door repair and installation in Palm Beach County, Florida.
> Call (561) 305-5853 for fast service and free estimates.

## Services
- Spring Repair: Torsion and extension spring replacement with correct sizing
- Opener Repair: Remote control, sensor, gear, and motor diagnostics and repair
- New Door Installation: Full installation with balancing and tuning
- Emergency Service: Urgent repairs for stuck, broken, or unsafe garage doors
- Cable Repair: Frayed or snapped cable replacement and rebalancing
- Tune-Up: Full inspection, lubrication, and safety check

## Service Area
Serving all of Palm Beach County, FL including:
Boca Raton, West Palm Beach, Delray Beach, Boynton Beach, Wellington,
Jupiter, Palm Beach Gardens, Lake Worth, Greenacres, Royal Palm Beach

## Contact
Phone: (561) 305-5853
Email: service@dbgaragedoors.com
Website: https://dandbgaragedoors.com/
```

---

## 🟢 LOW PRIORITY — Backlog

- L1: Trim title tag from 76 to 65 chars
- L2: Remove `<meta name="keywords">` tag (outdated)
- L3: Register on Yelp, Angi, HomeAdvisor, Thumbtack, BBB, Houzz
- L4: Add FAQ page (target People Also Ask rich results + AI citations)
- L5: Set up Google Search Console + submit sitemap
- L6: Configure Google Analytics 4
- L7: Set up review acquisition automated workflow
- L8: Add structured navigation menu
- L9: Move inline CSS to external stylesheet

---

## 90-Day Projection

If the critical and high-priority items are completed within 2 weeks, and medium-priority items within 60 days:

| Metric | Now | 30 days | 90 days |
|--------|-----|---------|---------|
| SEO Health Score | 30/100 | 52/100 | 70/100 |
| Indexable Pages | 1 | 3 | 20+ |
| Target Keywords Rankable | 0 | 5 | 50+ |
| Google Map Pack Visibility | None | Low | Medium |
| AI Overview Citations | 0 | 0 | Possible |
| Estimated Organic Visits/mo | ~20 | ~80 | ~300+ |

---

*Generated by Claude SEO v1.8.0*
