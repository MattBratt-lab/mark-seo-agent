/**
 * GET /get-blogs — JSON feed for the static site (js/main.js).
 * Requires D1 binding "DB" and table blog_posts (see migrations/).
 *
 * Response posts[] shape:
 * { slug, city, title, excerpt, content, created_at, published }
 * Prefer linking cards to `/blog/${slug}/` when slug is present.
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
  published: number | null;
};

/** Allow browser fetches from www, apex, and Cloudflare Pages preview hosts. */
function corsForRequest(request: Request): Record<string, string> {
  const origin = request.headers.get("Origin");
  if (!origin) return {};
  try {
    const h = new URL(origin).hostname.toLowerCase();
    if (h === "www.dandbgaragedoors.com" || h === "dandbgaragedoors.com") {
      return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Accept, Content-Type",
        Vary: "Origin",
      };
    }
    if (h.endsWith(".pages.dev")) {
      return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Accept, Content-Type",
        Vary: "Origin",
      };
    }
  } catch {
    /* ignore */
  }
  return {};
}

export const onRequestOptions: PagesFunction<Env> = async ({ request }) => {
  const c = corsForRequest(request);
  if (!c["Access-Control-Allow-Origin"]) {
    return new Response(null, { status: 403 });
  }
  return new Response(null, { status: 204, headers: c });
};

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { env, request } = context;
  const headers: Record<string, string> = {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "public, max-age=60",
    ...corsForRequest(request),
  };

  const db = env.DB;
  if (!db) {
    return Response.json(
      {
        ok: false,
        error:
          "D1 binding DB is missing on this Pages project. Dashboard → db-garage-doors → Settings → Functions → add D1 as DB.",
      },
      { status: 503, headers }
    );
  }

  try {
    const { results } = await db.prepare(
      `SELECT slug, city, title, excerpt, content, created_at, published
       FROM blog_posts
       WHERE COALESCE(published, 1) = 1
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
      published: row.published == null ? 1 : Number(row.published),
    }));

    const citySet = new Set<string>();
    for (const p of posts) {
      if (p.city) citySet.add(p.city);
    }
    const cities = Array.from(citySet).sort((a, b) => a.localeCompare(b));

    return Response.json({ ok: true, cities, posts }, { headers });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.includes("no such table")) {
      return Response.json({ ok: true, cities: [], posts: [] }, { headers });
    }
    return Response.json({ ok: false, error: msg }, { status: 500, headers });
  }
};
