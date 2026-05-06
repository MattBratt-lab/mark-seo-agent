/**
 * Writes sitemap.xml from every site index.html (repo root, excluding dist/node_modules).
 * lastmod = file mtime as YYYY-MM-DD (UTC). No priority/changefreq.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const BASE = "https://www.dandbgaragedoors.com";

/** URLs served by functions/blog/[slug].ts from D1 — keep in sync with scripts/build-blog-seed-sql.mjs */
const D1_BLOG_SLUGS = [
  "garage-door-repair-cost-palm-beach",
  "why-garage-door-spring-keeps-breaking",
  "garage-door-opener-troubleshooting",
  "garage-door-maintenance-checklist-florida",
  "diy-vs-professional-garage-door-repair",
  "garage-door-replace-vs-repair-signs",
  "garage-door-spring-lifespan-florida",
];

const SKIP_DIRS = new Set(["dist", "node_modules", ".git"]);

function walkIndexHtml(dir, out = []) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_DIRS.has(ent.name)) continue;
    const abs = path.join(dir, ent.name);
    if (ent.isDirectory()) walkIndexHtml(abs, out);
    else if (ent.name === "index.html") out.push(abs);
  }
  return out;
}

function toLoc(absFile) {
  const rel = path.relative(root, absFile).split(path.sep).join("/");
  if (rel === "index.html") return `${BASE}/`;
  const dir = rel.replace(/\/index\.html$/, "");
  return `${BASE}/${dir}/`;
}

/** Sitemap lastmod from filesystem mtime (UTC date only). */
function lastmodDate(absFile) {
  return new Date(fs.statSync(absFile).mtimeMs).toISOString().slice(0, 10);
}

function escapeXml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

const files = walkIndexHtml(root);
const entries = files.map((f) => ({ loc: toLoc(f), lastmod: lastmodDate(f) }));

const blogLastmod = new Date().toISOString().slice(0, 10);
for (const slug of D1_BLOG_SLUGS) {
  entries.push({ loc: `${BASE}/blog/${slug}/`, lastmod: blogLastmod });
}

entries.sort((a, b) => a.loc.localeCompare(b.loc));

let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
`;
for (const e of entries) {
  xml += `  <url>
    <loc>${escapeXml(e.loc)}</loc>
    <lastmod>${e.lastmod}</lastmod>
  </url>
`;
}
xml += `</urlset>
`;

const outPath = path.join(root, "sitemap.xml");
fs.writeFileSync(outPath, xml, "utf8");
console.log(`Wrote sitemap.xml (${entries.length} URLs from index.html mtimes)`);
