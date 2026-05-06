/**
 * Fetch production /get-blogs and print whether posts load or SQL errors appear.
 * Usage: node scripts/verify-get-blogs.mjs [url]
 */
const url = process.argv[2] || "https://www.dandbgaragedoors.com/get-blogs";

const res = await fetch(url, { headers: { Accept: "application/json" } });
const text = await res.text();
let body;
try {
  body = JSON.parse(text);
} catch {
  console.log(`HTTP ${res.status} — non-JSON body (first 200 chars):\n${text.slice(0, 200)}`);
  process.exit(1);
}

console.log(`URL: ${url}`);
console.log(`HTTP ${res.status}`);
if (body.error || body.success === false) {
  console.log(`Problem: ${body.error ?? JSON.stringify(body)}`);
}
const posts = body.posts ?? [];
console.log(`posts.length: ${Array.isArray(posts) ? posts.length : "n/a"}`);
if (Array.isArray(posts) && posts[0]) {
  console.log("first.slug:", posts[0].slug);
  console.log("first.title:", posts[0].title?.slice?.(0, 60));
}
