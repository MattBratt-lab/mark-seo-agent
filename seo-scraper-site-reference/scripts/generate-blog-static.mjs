/**
 * Build-time: inject crawlable blog cards into blog/index.html and homepage index.html
 * from data/blog-posts.json (+ built-in guide rows). Edit JSON when CMS/D1 content changes; re-run build.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const dataPath = path.join(root, "data", "blog-posts.json");

const CITY_HREF = {
  "Boca Raton": "/locations/boca-raton/",
  "West Palm Beach": "/locations/west-palm-beach/",
  "Delray Beach": "/locations/delray-beach/",
  "Boynton Beach": "/locations/boynton-beach/",
  Wellington: "/locations/wellington/",
  Jupiter: "/locations/jupiter/",
  "Palm Beach Gardens": "/locations/palm-beach-gardens/",
  "Lake Worth": "/locations/lake-worth/",
};

const STATIC_GUIDE_POSTS = [
  {
    city: "Guides",
    title: "Garage Door Repair Cost in Palm Beach County",
    excerpt: null,
    content:
      "Typical repair costs, what affects price, and when replacement makes sense for Palm Beach homeowners.",
    href: "/blog/garage-door-repair-cost-palm-beach/",
  },
];

function cityToHref(city) {
  const c = String(city || "").trim();
  if (CITY_HREF[c]) return CITY_HREF[c];
  return `/locations/${c.toLowerCase().replace(/\s+/g, "-")}/`;
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function excerptFromRow(row) {
  const ex = String(row.excerpt || "").trim();
  if (ex) return ex;
  const contentStr = String(row.content || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  return contentStr.length > 220 ? contentStr.slice(0, 220) + "…" : contentStr;
}

function cardHtml(row) {
  const rowCity = row.city || "";
  const title = String(row.title || "Service update").trim();
  const excerpt = excerptFromRow(row);
  const href = row.href || cityToHref(rowCity);
  const badge = rowCity ? `${escapeHtml(rowCity)}, FL` : "Palm Beach County";
  const moreText = row.href ? "Read the guide →" : `View ${rowCity || "area"} page →`;
  return (
    `<article class="glass-card p-6 flex flex-col gap-3 visible" role="listitem" data-blog-ssg-card="1">` +
    `<div class="text-xs font-bold uppercase tracking-wide text-primary-light">${badge}</div>` +
    `<h2 class="text-lg font-bold text-text-primary leading-snug">` +
    `<a href="${escapeHtml(href)}" class="inline-flex items-center min-h-12 py-2.5 -my-2.5 hover:text-primary-light transition-colors">${escapeHtml(title)}</a></h2>` +
    `<p class="text-sm text-text-muted leading-relaxed line-clamp-5">${escapeHtml(excerpt)}</p>` +
    `<a href="${escapeHtml(href)}" class="inline-flex items-center gap-1 min-h-12 py-[15px] -my-[15px] text-sm font-semibold text-primary-light hover:text-primary mt-auto">${escapeHtml(moreText)}</a>` +
    `</article>`
  );
}

function cityPillHtml(city) {
  const href = cityToHref(city);
  return (
    `<a href="${escapeHtml(href)}" class="cursor-pointer rounded-full border border-border-glass bg-surface-glass px-4 py-2 text-sm font-semibold backdrop-blur-sm transition-all duration-200 hover:border-primary/30 hover:bg-white/[0.08]">${escapeHtml(city)}</a>`
  );
}

function loadJsonPosts() {
  try {
    const raw = fs.readFileSync(dataPath, "utf8");
    const j = JSON.parse(raw);
    return Array.isArray(j.posts) ? j.posts : [];
  } catch {
    return [];
  }
}

function mergedRows() {
  return [...STATIC_GUIDE_POSTS, ...loadJsonPosts()];
}

function uniqueCities(rows) {
  const s = new Set();
  for (const r of rows) {
    const c = String(r.city || "").trim();
    if (c && c !== "Guides") s.add(c);
  }
  return Array.from(s).sort((a, b) => a.localeCompare(b));
}

function main() {
  const rows = mergedRows();
  const cities = uniqueCities(rows);
  const cardsHtml = rows.map(cardHtml).join("\n            ");
  const citiesHtml = cities.map(cityPillHtml).join("\n            ");

  const blogPath = path.join(root, "blog", "index.html");
  let blogHtml = fs.readFileSync(blogPath, "utf8");
  const reBlogCities = /<!--blog-ssg:cities:start-->([\s\S]*?)<!--blog-ssg:cities:end-->/;
  const reBlogGrid = /<!--blog-ssg:grid:start-->([\s\S]*?)<!--blog-ssg:grid:end-->/;
  if (!reBlogCities.test(blogHtml) || !reBlogGrid.test(blogHtml)) {
    console.error("blog/index.html missing blog-ssg marker comments");
    process.exit(1);
  }
  blogHtml = blogHtml.replace(
    reBlogCities,
    `<!--blog-ssg:cities:start-->\n            ${citiesHtml}\n            <!--blog-ssg:cities:end-->`
  );
  blogHtml = blogHtml.replace(
    reBlogGrid,
    `<!--blog-ssg:grid:start-->\n            ${cardsHtml}\n            <!--blog-ssg:grid:end-->`
  );
  fs.writeFileSync(blogPath, blogHtml, "utf8");
  console.log("Wrote static blog listing to blog/index.html");

  const indexPath = path.join(root, "index.html");
  let indexHtml = fs.readFileSync(indexPath, "utf8");
  const reHome = /<!--home-blog-ssg:start-->([\s\S]*?)<!--home-blog-ssg:end-->/;
  if (!reHome.test(indexHtml)) {
    console.error("index.html missing home-blog-ssg marker comments");
    process.exit(1);
  }
  const homeRows = rows.slice(0, 6);
  const homeCards = homeRows.map(cardHtml).join("\n            ");
  indexHtml = indexHtml.replace(
    reHome,
    `<!--home-blog-ssg:start-->\n            ${homeCards}\n            <!--home-blog-ssg:end-->`
  );
  if (!indexHtml.includes("data-home-blog-prerendered")) {
    indexHtml = indexHtml.replace("<html lang=\"en\">", '<html lang="en" data-home-blog-prerendered="true">');
  }
  fs.writeFileSync(indexPath, indexHtml, "utf8");
  console.log("Wrote static blog cards to index.html (home section, max 6)");
}

main();
