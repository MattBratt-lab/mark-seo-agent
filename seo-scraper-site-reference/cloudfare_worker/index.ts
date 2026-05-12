/**
 * Standalone Worker (optional). Prefer Pages Functions ../functions/get-blogs.ts when
 * deploying the static site with `wrangler pages deploy`. If both are active, zone
 * Worker routes run first — remove Worker routes for /get-blogs* or delete this deploy.
 */
interface Env {
  DB: D1Database;
}

type Row = {
  slug: string | null;
  city: string | null;
  title: string | null;
  excerpt: string | null;
  content: string | null;
  created_at: string | null;
};

function normalizePath(pathname: string): string {
  let p = pathname;
  if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
  return p || "/";
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const path = normalizePath(new URL(request.url).pathname);
    if (request.method !== "GET" || path !== "/get-blogs") {
      return new Response("Not Found", { status: 404 });
    }

    const headers = {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=60",
    };

    try {
      const { results } = await env.DB.prepare(
        `SELECT slug, city, title, excerpt, content, created_at
         FROM blog_posts
         ORDER BY datetime(created_at) DESC
         LIMIT 100`
      ).all<Row>();

      const posts = (results ?? []).map((row) => ({
        slug: String(row.slug ?? "").trim(),
        city: String(row.city ?? "").trim(),
        title: String(row.title ?? "").trim(),
        excerpt: String(row.excerpt ?? "").trim(),
        content: String(row.content ?? "").trim(),
        created_at: row.created_at ?? "",
        published: 1,
      }));

      const citySet = new Set<string>();
      for (const p of posts) {
        if (p.city) citySet.add(p.city);
      }
      const cities = Array.from(citySet).sort((a, b) => a.localeCompare(b));

      return Response.json({ ok: true, success: true, cities, posts }, { headers });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes("no such table")) {
        return Response.json({ ok: true, success: true, cities: [], posts: [] }, { headers });
      }
      return Response.json({ ok: false, success: false, posts: [], cities: [], error: msg }, { status: 500, headers });
    }
  },
};
