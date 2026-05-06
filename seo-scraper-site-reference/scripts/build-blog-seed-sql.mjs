/**
 * Writes migrations/0002_seed_blog_posts.sql with INSERTs for blog_posts.
 * Run: node scripts/build-blog-seed-sql.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const outPath = path.join(root, "migrations", "0002_seed_blog_posts.sql");

function esc(val) {
  return "'" + String(val).replace(/'/g, "''") + "'";
}

/** @type {{ slug: string; city: string; title: string; excerpt: string; content: string; created_at: string }[]} */
const posts = [
  {
    slug: "garage-door-repair-cost-palm-beach",
    city: "Guides",
    title: "How Much Does Garage Door Repair Cost in Palm Beach County?",
    excerpt:
      "Typical repair ranges in Palm Beach County, what drives price (springs, openers, cables), and when replacement is the smarter investment.",
    created_at: "2026-05-01T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Garage door repair pricing around Palm Beach County depends on the repair type, hardware condition, and whether the door can be tuned safely without full replacement. Below is a practical framework homeowners use before approving work.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Common repair categories</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li><strong>Spring replacement</strong> — Often the largest single repair line item because springs are under extreme tension and must be matched to door weight.</li>
<li><strong>Opener diagnostics</strong> — Motors, logic boards, gears, and safety sensors each present different cost profiles.</li>
<li><strong>Cable and roller work</strong> — Usually smaller parts cost but labor reflects careful rebalancing.</li>
<li><strong>Track and roller adjustments</strong> — Noise, binding, and uneven wear can sometimes be corrected without new panels.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">What affects the total bill</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Door size, weight, and one-piece versus sectional construction.</li>
<li>Single versus double-wide bays and ceiling height constraints.</li>
<li>Corrosion from coastal humidity and storm-season moisture.</li>
<li>Emergency timing versus scheduled maintenance visits.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">Repair versus replacement</h2>
<p class="text-text-muted leading-relaxed">If panels are heavily damaged, tracks are bent repeatedly, or an older door lacks modern safety features, replacement may reduce lifetime cost versus stacking repairs. A qualified technician should document measurements and spring specs before quoting.</p>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. For a written estimate in Palm Beach County, call <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
  {
    slug: "why-garage-door-spring-keeps-breaking",
    city: "Guides",
    title: "Why Your Garage Door Spring Keeps Breaking (and How to Stop the Cycle)",
    excerpt:
      "Cycle life, garage humidity, mismatched springs, and skipped tune-ups — what actually causes repeat spring failures in Florida.",
    created_at: "2026-05-03T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Repeat spring failures are frustrating and dangerous. In South Florida, humidity, salt air near the coast, and heavy daily use accelerate wear. Here is how to break the cycle.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Normal wear versus early failure</h2>
<p class="text-text-muted leading-relaxed">Springs are rated in cycles. If usage is high (multiple trips per day), expected life arrives sooner. Early failure often signals imbalance, wrong spring specification, or hardware dragging.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Common repeat-break causes</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li><strong>Mismatched spring pairs</strong> — Uneven lift strains one spring.</li>
<li><strong>Frayed cables or sticking rollers</strong> — Extra friction wears coils unevenly.</li>
<li><strong>Corrosion</strong> — Surface rust weakens wire over time.</li>
<li><strong>DIY partial fixes</strong> — Replacing only one spring on a dual system without verification.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">What helps</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Annual tune-ups with balance checks and lubrication suited to your hardware.</li>
<li>Replace cables when springs are serviced if wear is visible.</li>
<li>Address opener force limits only after the door is verified balanced.</li>
</ul>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. Safe spring service in Palm Beach County: <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
  {
    slug: "garage-door-opener-troubleshooting",
    city: "Guides",
    title: "Garage Door Opener Troubleshooting: Problems You Can Diagnose Before Calling",
    excerpt:
      "Remote checks, safety sensors, manual disconnect, and breaker tests — a sane order of operations before requesting service.",
    created_at: "2026-05-05T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Before assuming the opener motor failed, rule out quick fixes that take minutes. Always stay clear of moving parts and never bypass safety sensors for routine use.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Start here</h2>
<ol class="list-decimal pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Confirm the opener unit has power (GFCI outlet, breaker).</li>
<li>Test the wall button — if it works but remotes do not, suspect remote batteries or programming.</li>
<li>Check sensor alignment — LEDs usually indicate blocked or misaligned photo eyes.</li>
<li>Listen for motor hum without travel — could indicate a stripped gear or bound door.</li>
</ol>
<h2 class="text-xl font-bold text-text-primary mt-8">When to stop and call a pro</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Door feels heavy when lifted manually after disconnect.</li>
<li>Broken spring suspected.</li>
<li>Repeated opener overheating or breaker trips.</li>
</ul>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. Opener diagnostics and repair: <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
  {
    slug: "garage-door-maintenance-checklist-florida",
    city: "Guides",
    title: "Garage Door Maintenance Checklist for Florida Homeowners",
    excerpt:
      "Humidity, storms, and UV create a Florida-specific maintenance plan — inspection points you can track seasonally.",
    created_at: "2026-05-06T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Florida climate stresses metal hardware and electronics differently than cold climates. Use this checklist quarterly and after major storms.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Visual inspection</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Springs — gaps or elongation in coils.</li>
<li>Cables — fraying or rust flakes.</li>
<li>Rollers — cracks or wobble in wheels.</li>
<li>Weather seals — cracking at bottom astragal.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">Operation checks</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Door should stay halfway open when released mid-travel (balance).</li>
<li>Auto-reverse should engage when obstructed.</li>
<li>Listen for grinding — often rollers or hinges.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">Lubrication notes</h2>
<p class="text-text-muted leading-relaxed">Use products appropriate for your hardware type; avoid greasing tracks where rollers need clean rolling surfaces. When unsure, have a technician apply spec-correct lubricants during a tune-up.</p>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. Schedule tune-ups: <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
  {
    slug: "diy-vs-professional-garage-door-repair",
    city: "Guides",
    title: "DIY vs Professional Garage Door Repair: What Is Safe to Attempt?",
    excerpt:
      "Which tasks are homeowner-friendly versus high-risk (springs, cables, winding bars) under Florida safety norms.",
    created_at: "2026-05-07T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Garage doors are heavy and springs store lethal energy. Knowing where DIY ends prevents injuries and property damage.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Generally reasonable homeowner tasks</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Remote programming and battery swaps.</li>
<li>Clearing debris from tracks (without bending metal).</li>
<li>Tightening obvious loose fasteners on hinges — gently, without stripping.</li>
<li>Light bulb replacement in opener housing when accessible.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">Leave to licensed technicians</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Torsion or extension spring replacement or adjustment.</li>
<li>Cable winding or drum work.</li>
<li>Track radius repair after impact.</li>
<li>Structural panel hinge failures on oversized doors.</li>
</ul>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. Professional repairs across Palm Beach County: <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
  {
    slug: "garage-door-replace-vs-repair-signs",
    city: "Guides",
    title: "Signs You Need a New Garage Door vs When Repair Is Enough",
    excerpt:
      "Panel damage, insulation goals, recurring breakdowns, and safety upgrades — clear decision signals for replacement.",
    created_at: "2026-05-08T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Replacement is not always cosmetic; sometimes it is the economical choice after repeated component failures or corrosion.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Repair-first scenarios</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Single component failure on an otherwise sound door.</li>
<li>Noisy operation from rollers or hinges.</li>
<li>Minor sensor or opener issues.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">Consider replacement</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Multiple rotted or rusted panels.</li>
<li>Door lacks pinch resistance or modern safety features you want.</li>
<li>Poor insulation drives garage heat load.</li>
<li>Structural sagging that cannot be shimmed safely.</li>
</ul>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. Honest repair versus replace guidance: <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
  {
    slug: "garage-door-spring-lifespan-florida",
    city: "Guides",
    title: "How Long Do Garage Door Springs Last in Florida?",
    excerpt:
      "Cycle ratings, coastal corrosion, and maintenance habits — realistic lifespan expectations for Palm Beach County.",
    created_at: "2026-05-09T14:00:00Z",
    content: `
<section class="blog-body space-y-6">
<p class="text-text-muted leading-relaxed">Springs do not die on a calendar date; they die in cycles modified by environment and maintenance.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Understanding cycle life</h2>
<p class="text-text-muted leading-relaxed">Manufacturers rate springs for a number of open-close cycles. A household that cycles the door many times daily reaches that count sooner than a twice-daily pattern.</p>
<h2 class="text-xl font-bold text-text-primary mt-8">Florida-specific factors</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>Humidity accelerates surface corrosion even indoors.</li>
<li>Coastal properties see faster hardware oxidation.</li>
<li>Hurricane prep cycles (opening for shutters, storage) add usage spikes.</li>
</ul>
<h2 class="text-xl font-bold text-text-primary mt-8">Warning signs</h2>
<ul class="list-disc pl-6 space-y-2 text-text-muted leading-relaxed">
<li>A loud snap from the garage.</li>
<li>Door rises only a few inches before stopping.</li>
<li>Visible gap in a torsion spring coil.</li>
</ul>
<p class="text-text-muted leading-relaxed"><strong>D&amp;B Garage Doors</strong> — Florida license <strong>#CGC1519508</strong>. Spring inspection and replacement: <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>.</p>
</section>`.trim(),
  },
];

let sql = `-- Seed blog posts (idempotent). Run after 0001_blog_posts.sql.\n`;
sql += `DELETE FROM blog_posts WHERE slug IN (${posts.map((p) => esc(p.slug)).join(", ")});\n\n`;

for (const p of posts) {
  sql +=
    `INSERT INTO blog_posts (slug, city, title, excerpt, content, created_at) VALUES (` +
    `${esc(p.slug)}, ${esc(p.city)}, ${esc(p.title)}, ${esc(p.excerpt)}, ${esc(p.content)}, ${esc(p.created_at)});\n`;
}

fs.writeFileSync(outPath, sql, "utf8");
console.log(`Wrote ${outPath} (${posts.length} posts)`);
