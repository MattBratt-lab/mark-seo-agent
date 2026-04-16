/**
 * Quick checks from your machine (does not fix Cloudflare — only reports status).
 * Usage: node scripts/health-check.mjs
 */
import https from "node:https";

const URLS = [
  "https://db-garage-doors.pages.dev/get-blogs",
  "https://db-garage-doors.pages.dev/blog/",
  "https://www.dandbgaragedoors.com/get-blogs",
  "https://www.dandbgaragedoors.com/blog/",
];

function get(url) {
  return new Promise((resolve) => {
    const req = https.get(
      url,
      { timeout: 12000, headers: { "User-Agent": "seo-scraper-bot-health-check" } },
      (res) => {
        let body = "";
        res.on("data", (c) => {
          body += c;
          if (body.length > 500) body = body.slice(0, 500);
        });
        res.on("end", () => resolve({ url, status: res.statusCode, snippet: body.trim().slice(0, 120) }));
      }
    );
    req.on("timeout", () => {
      req.destroy();
      resolve({ url, status: "TIMEOUT" });
    });
    req.on("error", (e) => resolve({ url, status: "ERROR", error: e.message }));
  });
}

console.log("Checking endpoints…\n");
for (const u of URLS) {
  const r = await get(u);
  const line =
    r.status === "ERROR"
      ? `ERROR  ${u}\n       ${r.error}`
      : `${String(r.status).padEnd(6)} ${u}${r.snippet ? "\n       " + JSON.stringify(r.snippet) : ""}`;
  console.log(line + "\n");
}
