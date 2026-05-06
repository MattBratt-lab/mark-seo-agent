# Site Structure — Garage Door Local Service Business
**Template:** local-service.md  
**Date:** 2026-04-01

---

## URL Hierarchy (33 Core Pages)

```
https://dandbgaragedoors.com/
│
├── / (Homepage)
│   └── Target: "garage door repair Palm Beach County" + brand
│
├── /about/
│   └── Target: brand + trust signals, E-E-A-T
│
├── /contact/
│   └── Target: "contact garage door repair Palm Beach"
│
├── /reviews/
│   └── Target: "D & B Garage Doors reviews", social proof
│
├── /gallery/
│   └── Target: "garage door installation photos Palm Beach"
│
├── /faq/
│   └── Target: long-tail Q&A, People Also Ask
│
├── /emergency/
│   └── Target: "emergency garage door repair 24/7 Palm Beach"
│
├── /services/
│   ├── /services/garage-door-spring-repair/
│   │   └── Target: "garage door spring repair Palm Beach County"
│   ├── /services/garage-door-opener-repair/
│   │   └── Target: "garage door opener repair Palm Beach"
│   ├── /services/garage-door-installation/
│   │   └── Target: "garage door installation Palm Beach County"
│   ├── /services/garage-door-cable-repair/
│   │   └── Target: "garage door cable repair Palm Beach"
│   ├── /services/garage-door-tune-up/
│   │   └── Target: "garage door maintenance tune up Palm Beach"
│   └── /services/garage-door-replacement/
│       └── Target: "garage door replacement Palm Beach County"
│
├── /locations/
│   ├── /locations/boca-raton/
│   │   └── Target: "garage door repair Boca Raton FL"
│   ├── /locations/west-palm-beach/
│   │   └── Target: "garage door repair West Palm Beach"
│   ├── /locations/delray-beach/
│   │   └── Target: "garage door repair Delray Beach FL"
│   ├── /locations/boynton-beach/
│   │   └── Target: "garage door repair Boynton Beach FL"
│   ├── /locations/wellington/
│   │   └── Target: "garage door repair Wellington FL"
│   ├── /locations/jupiter/
│   │   └── Target: "garage door repair Jupiter FL"
│   ├── /locations/palm-beach-gardens/
│   │   └── Target: "garage door repair Palm Beach Gardens"
│   ├── /locations/lake-worth/
│   │   └── Target: "garage door repair Lake Worth FL"
│   ├── /locations/greenacres/
│   │   └── Target: "garage door repair Greenacres FL"
│   └── /locations/royal-palm-beach/
│       └── Target: "garage door repair Royal Palm Beach FL"
│
├── /blog/
│   └── (20-40 posts over 6 months — see CONTENT-CALENDAR.md)
│
├── /sitemap.xml
├── /robots.txt
└── /llms.txt
```

**Total core pages: 33**  
**With blog posts (6 months): 53-73**

> ⚠️ **Quality Gate Check:** 10 location pages — well under the 30-page WARNING threshold. All pass.

---

## Page Specifications

### Homepage `/`
- **Word count target:** 800-1,200 words
- **H1:** "Garage Door Repair & Installation — Palm Beach County, FL"
- **Schema:** HomeAndConstructionBusiness + WebSite
- **Key sections:**
  - Hero: H1 + phone CTA + service area statement
  - Services overview grid (link to service pages)
  - Service area map / city list (link to location pages)
  - Reviews / star rating widget
  - About/trust section (license, years, photos)
  - Emergency CTA banner
  - FAQ snippet (3-5 questions)

### Service Pages `/services/[service]/`
- **Word count target:** 800-1,200 words each
- **H1 pattern:** "[Service Name] in Palm Beach County, FL"
- **Schema:** Service + LocalBusiness
- **Key sections:**
  - What the service is + when you need it
  - Our process (step-by-step)
  - Pricing factors / cost range
  - Safety information (relevant for springs)
  - Service area (list cities)
  - CTA with phone
  - 3-5 FAQs about that service
  - Related services (internal links)
- **Internal links:** Link to 2-3 related city pages + other service pages

### Location Pages `/locations/[city]/`
- **Word count target:** 600-800 words each (minimum 500)
- **Unique content requirement:** 60%+ unique per quality gate
- **H1 pattern:** "Garage Door Repair in [City], FL | D & B Garage Doors"
- **Schema:** LocalBusiness with city in areaServed
- **Key sections:**
  - City-specific intro (mention neighborhoods, landmarks)
  - Services available in that city
  - Why choose us for [city] (local angle)
  - Service times / response area
  - City-specific testimonial (if available)
  - Map embed (Google Maps of service area)
  - Emergency CTA
  - FAQs for that city
- **Internal links:** Link to all service pages + neighboring city pages

### About Page `/about/`
- **Word count target:** 600-900 words
- **Must include:** Founding story, years in business, license number, insurance statement, team photo, technician certifications, service area rationale
- **Schema:** LocalBusiness + Person (founder)

### Emergency Page `/emergency/`
- **Word count target:** 400-600 words
- **H1:** "24/7 Emergency Garage Door Repair — Palm Beach County"
- **Above the fold:** Phone number, expected response time, "we're available now" signal
- **Schema:** Service + Emergency declaration
- **Priority note:** This page often ranks for the highest-urgency (and highest-converting) queries

### FAQ Page `/faq/`
- **Word count target:** 1,500-2,000 words (15-20 questions)
- **Note per skill rules:** FAQPage schema not recommended for Google rich results on commercial sites (Aug 2023 restriction). Add content but skip FAQPage schema. Structure benefits AI/LLM citation.

---

## Internal Linking Matrix

| Source Page | Must Link To | Should Link To |
|-------------|-------------|----------------|
| Homepage | All 6 service pages, all 8 city pages, /emergency, /about, /reviews | /blog (recent posts), /faq |
| Service pages | /emergency, /contact, /reviews | 2-3 city pages, 2-3 related service pages, /faq |
| City pages | All 6 service pages, /contact, /emergency | 2-3 neighboring city pages, /reviews |
| Blog posts | 1-2 relevant service pages, 1-2 relevant city pages | /faq, /about, /reviews |
| About | /contact, /reviews, /gallery | All service pages |
| Emergency | /contact, all service pages | All city pages |

---

## Sitemap Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://dandbgaragedoors.com/sitemap-core.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://dandbgaragedoors.com/sitemap-locations.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://dandbgaragedoors.com/sitemap-blog.xml</loc>
  </sitemap>
</sitemapindex>
```

Split into 3 sitemaps once blog launches. Core sitemap covers homepage + service pages + about/contact/reviews/faq/emergency. Location sitemap covers all 8 city pages. Blog sitemap auto-generated.

---

## Navigation Design

```
[Logo — D&B]  [Services ▾]  [Locations ▾]  [About]  [Reviews]  [Blog]  [(561) 305-5853 ← CTA button]

Services dropdown:
  Spring Repair | Opener Repair | Installation | Cable Repair | Tune-Up | Emergency Service

Locations dropdown:
  Boca Raton | West Palm Beach | Delray Beach | Boynton Beach | Wellington
  Jupiter | Palm Beach Gardens | Lake Worth | All Service Areas →
```

Footer:
```
[Services column]  [Locations column]  [Company column]  [Contact column]
                         (561) 305-5853
                   service@dbgaragedoors.com
                   © D & B Garage Doors
```
