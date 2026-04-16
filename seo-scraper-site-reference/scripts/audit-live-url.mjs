/**
 * Live URL checks + weighted score (/100) for NAP, schema, and crawl basics.
 * Usage: node scripts/audit-live-url.mjs [https://www.example.com]
 */
import https from "node:https";

const BASE = (process.argv[2] || "https://www.dandbgaragedoors.com").replace(/\/$/, "");

/** @typedef {{ name: string, points: number, pass: boolean, detail?: string }} Check */

function get(path) {
  return new Promise((resolve, reject) => {
    const url = BASE + path;
    https
      .get(url, { timeout: 20000, headers: { "User-Agent": "seo-scraper-bot-audit/1.0" } }, (res) => {
        let body = "";
        res.on("data", (c) => (body += c));
        res.on("end", () => resolve({ url, status: res.statusCode, body }));
      })
      .on("error", reject)
      .on("timeout", function () {
        this.destroy();
        reject(new Error("timeout"));
      });
  });
}

function extractLdJson(html) {
  const blocks = [];
  const re = new RegExp(
    '<script[^>]*type=["\']application/ld\\+json["\'][^>]*>([\\s\\S]*?)</script>',
    "gi"
  );
  let m;
  while ((m = re.exec(html))) blocks.push(m[1].trim());
  return blocks;
}

/** @type {Check[]} */
const checks = [];

const home = await get("/");
checks.push({
  name: "Homepage responds HTTP 200",
  points: 15,
  pass: home.status === 200,
  detail: home.status === 200 ? undefined : `got ${home.status}`,
});

const html = home.body || "";
checks.push({
  name: "Visible phone (561) 305-0877 in HTML",
  points: 10,
  pass: html.includes("305-0877"),
});
checks.push({
  name: "Email anthony@dbgaragedoors.us in HTML",
  points: 10,
  pass: html.includes("anthony@dbgaragedoors.us"),
});
checks.push({
  name: "Clickable tel:+15613050877",
  points: 10,
  pass: html.includes("tel:+15613050877"),
});

const ldBlocks = extractLdJson(html);
checks.push({
  name: "At least one JSON-LD block",
  points: 10,
  pass: ldBlocks.length > 0,
  detail: ldBlocks.length ? `${ldBlocks.length} block(s)` : undefined,
});

let allLdValid = ldBlocks.length > 0;
let ldParseError = "";
for (let i = 0; i < ldBlocks.length; i++) {
  try {
    JSON.parse(ldBlocks[i]);
  } catch (e) {
    allLdValid = false;
    if (!ldParseError) ldParseError = `block ${i + 1}: ${e.message}`;
  }
}
checks.push({
  name: "All JSON-LD blocks parse as valid JSON",
  points: 15,
  pass: ldBlocks.length > 0 && allLdValid,
  detail: ldParseError || undefined,
});

let biz = null;
if (ldBlocks.length && allLdValid) {
  try {
    const g = JSON.parse(ldBlocks[0]);
    const graph = g["@graph"] || [];
    biz = graph.find((n) => {
      const t = n["@type"];
      const arr = Array.isArray(t) ? t : [t];
      return arr.some((x) => /LocalBusiness|HomeAndConstructionBusiness/.test(String(x)));
    });
  } catch {
    biz = null;
  }
}

checks.push({
  name: "JSON-LD includes LocalBusiness (or HomeAndConstructionBusiness)",
  points: 10,
  pass: Boolean(biz),
});

checks.push({
  name: "Schema telephone is +15613050877",
  points: 10,
  pass: biz?.telephone === "+15613050877",
  detail: biz && biz.telephone !== "+15613050877" ? String(biz.telephone) : undefined,
});

checks.push({
  name: "Schema email is anthony@dbgaragedoors.us",
  points: 10,
  pass: biz?.email === "anthony@dbgaragedoors.us",
  detail: biz && biz.email !== "anthony@dbgaragedoors.us" ? String(biz.email) : undefined,
});

const ar = biz?.aggregateRating;
const ratingOk = ar != null && String(ar.ratingValue) === "4.6";
checks.push({
  name: "aggregateRating.ratingValue is 4.6",
  points: 10,
  pass: ratingOk,
  detail: !ratingOk && ar ? `ratingValue=${JSON.stringify(ar.ratingValue)}` : ar == null ? "missing" : undefined,
});

const robots = await get("/robots.txt");
checks.push({
  name: "robots.txt returns 200",
  points: 5,
  pass: robots.status === 200,
  detail: robots.status !== 200 ? `HTTP ${robots.status}` : undefined,
});

const sm = await get("/sitemap.xml");
checks.push({
  name: "sitemap.xml returns 200",
  points: 5,
  pass: sm.status === 200,
  detail: sm.status !== 200 ? `HTTP ${sm.status}` : undefined,
});

const maxPoints = checks.reduce((s, c) => s + c.points, 0);
const earned = checks.filter((c) => c.pass).reduce((s, c) => s + c.points, 0);
const score = maxPoints > 0 ? Math.round((earned / maxPoints) * 100) : 0;

console.log(`\n=== Live audit: ${BASE}/ ===\n`);
console.log(`OVERALL SCORE: ${score}/100  (${earned} / ${maxPoints} points)\n`);

console.log("Checks:");
for (const c of checks) {
  const icon = c.pass ? "✓" : "✗";
  const pts = c.points ? ` [${c.points} pts]` : "";
  const extra = c.detail ? ` — ${c.detail}` : "";
  console.log(`  ${icon} ${c.name}${pts}${extra}`);
}

const failed = checks.filter((c) => !c.pass);
if (failed.length) {
  console.log(`\n${failed.length} check(s) failed.`);
  process.exitCode = 1;
} else {
  console.log("\nAll checks passed.");
}

console.log("\nNote: This score only reflects these automated checks (not full Semrush/Lighthouse).");
console.log("Rich Results: https://search.google.com/test/rich-results");
