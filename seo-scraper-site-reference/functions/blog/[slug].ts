/**
 * Dynamic article pages backed by D1 (blog_posts.slug).
 * Requires Pages project binding DB → garage-db (see wrangler.toml).
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

function escapeHtml(str: string): string {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const paramSlug = typeof context.params.slug === "string" ? context.params.slug.trim() : "";
  const slug = paramSlug;

  if (!slug || slug.includes("/") || slug.includes("..")) {
    return new Response("Not Found", { status: 404, headers: { "content-type": "text/plain;charset=UTF-8" } });
  }

  const db = context.env.DB;
  if (!db) {
    return new Response("Blog database unavailable", {
      status: 503,
      headers: { "content-type": "text/plain;charset=UTF-8" },
    });
  }

  let row: Row | null = null;
  try {
    row = await db
      .prepare(
        `SELECT slug, city, title, excerpt, content, created_at
         FROM blog_posts WHERE slug = ? AND COALESCE(published, 1) = 1`
      )
      .bind(slug)
      .first<Row>();
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(`Blog query error: ${escapeHtml(msg)}`, {
      status: 500,
      headers: { "content-type": "text/html;charset=UTF-8" },
    });
  }

  if (!row || !row.title || !row.content) {
    return new Response("Not Found", { status: 404, headers: { "content-type": "text/plain;charset=UTF-8" } });
  }

  const title = String(row.title);
  const city = String(row.city ?? "").trim();
  const excerpt = String(row.excerpt ?? "").trim();
  const canonicalPath = `/blog/${slug}/`;
  const canonicalUrl = `https://www.dandbgaragedoors.com${canonicalPath}`;
  const safeTitle = escapeHtml(title);
  const metaDesc = excerpt.slice(0, 300) || title;

  const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${safeTitle} | D &amp; B Garage Doors</title>
    <meta name="description" content="${escapeHtml(metaDesc)}" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="canonical" href="${escapeHtml(canonicalUrl)}" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="${safeTitle}" />
    <meta property="og:description" content="${escapeHtml(metaDesc)}" />
    <meta property="og:url" content="${escapeHtml(canonicalUrl)}" />
    <meta property="og:site_name" content="D &amp; B Garage Doors" />
    <script type="application/ld+json">
${JSON.stringify({
  "@context": "https://schema.org",
  "@type": "Article",
  headline: title,
  description: metaDesc,
  datePublished: row.created_at ?? undefined,
  author: { "@type": "Organization", name: "D & B Garage Doors" },
  publisher: { "@type": "Organization", name: "D & B Garage Doors" },
  mainEntityOfPage: { "@type": "WebPage", "@id": canonicalUrl },
})}
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&amp;display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="/css/style.css" />
    <link rel="stylesheet" href="/css/tailwind.min.css" />
  </head>
  <body class="font-sans">
    <a class="skip" href="#main">Skip to content</a>
    <nav class="fixed top-4 left-4 right-4 z-50 mx-auto max-w-7xl" aria-label="Site header">
      <div class="glass-card flex items-center justify-between px-5 py-3">
        <a href="/" class="flex items-center gap-3 cursor-pointer" aria-label="D &amp; B Garage Doors home">
          <div class="h-10 w-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 border border-primary/50 flex items-center justify-center font-bold text-sm text-primary-light shadow-lg" aria-hidden="true">D&amp;B</div>
          <div class="hidden sm:block">
            <div class="font-bold text-sm tracking-tight">D &amp; B Garage Doors</div>
            <div class="text-xs text-text-muted">Palm Beach County, FL</div>
          </div>
        </a>
        <div class="hidden md:flex items-center gap-7 text-sm text-text-muted">
          <a href="/#services" class="cursor-pointer transition-colors duration-200 hover:text-text-primary">Services</a>
          <a href="/#service-areas" class="cursor-pointer transition-colors duration-200 hover:text-text-primary">Areas</a>
          <a href="/blog/" class="cursor-pointer transition-colors duration-200 hover:text-text-primary">Blog</a>
          <a href="/#contact" class="cursor-pointer transition-colors duration-200 hover:text-text-primary">Contact</a>
        </div>
        <a href="tel:+15613055853" class="js-phone-link cursor-pointer rounded-full bg-gradient-to-r from-primary to-primary-dark px-5 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:shadow-[0_0_24px_rgba(220,38,38,0.4)]">
          <span class="js-phone-display">(561) 305-5853</span>
        </a>
      </div>
    </nav>

    <main id="main" class="pt-28 pb-16 px-6">
      <article class="mx-auto max-w-3xl">
        <p class="text-xs font-bold uppercase tracking-wide text-primary-light mb-3">${escapeHtml(city ? `${city}` : "Guides")}</p>
        <h1 class="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary mb-4">${safeTitle}</h1>
        ${row.created_at ? `<p class="text-sm text-text-muted mb-10">${escapeHtml(row.created_at.slice(0, 10))}</p>` : ""}
        <div class="glass-card border-primary/15 overflow-hidden p-6 sm:p-8">
          ${row.content}
        </div>
        <p class="mt-10 text-sm text-text-muted">
          <a href="/blog/" class="text-primary-light font-semibold hover:text-primary">← Back to blog</a>
        </p>
      </article>
    </main>

    <footer class="border-t border-border-glass py-10" aria-label="Footer">
      <div class="mx-auto max-w-7xl px-6 text-sm text-text-muted">
        <strong class="text-text-primary">D &amp; B Garage Doors</strong> — Florida license #CGC1519508 ·
        <a href="tel:+15613055853" class="text-primary-light hover:text-primary">(561) 305-5853</a>
      </div>
    </footer>
    <script src="/js/main.js"></script>
  </body>
</html>`;

  return new Response(html, {
    headers: {
      "content-type": "text/html;charset=UTF-8",
      "cache-control": "public, max-age=300",
    },
  });
};
