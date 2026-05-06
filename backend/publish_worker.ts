// @ts-nocheck — add @cloudflare/workers-types in your deploy project for stricter typing
export interface Env {
  AI: Ai;
  AUTH_TOKEN: string;
  GITHUB_TOKEN: string;
  GITHUB_REPO: string;   // "owner/repo"
  GITHUB_BRANCH: string; // defaults to "main"
}

type PublishBody = {
  markdown?: string;
  city?: string;
  targetPath?: string;
  /** When set, commit this HTML as-is (topical hub). Do not use with location ``markdown`` flow. */
  html?: string;
  /** URL slug for default path ``guides/{hubSlug}/index.html``. */
  hubSlug?: string;
};

type GitHubFileResponse = {
  sha?: string;
};

// Convert **bold** and bare paragraphs to HTML <p> tags matching the site's glass-card style
function mdParagraphsToHtml(md: string, cssClass = "text-sm text-text-muted leading-relaxed"): string[] {
  return md
    .split(/\n{2,}/)
    .map(block => block.trim())
    .filter(block => block && !block.startsWith("#") && !block.startsWith("---"))
    .map(block => {
      const inner = block
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br />");
      return `<p class="${cssClass}">${inner}</p>`;
    });
}

function buildLocationHtml(city: string, citySlug: string, paragraphs: string[]): string {
  const heroParagraphs = paragraphs.slice(0, 4).join("\n                ");
  const ctaParagraphs = paragraphs.slice(4).join("\n            ");
  const metaDesc = `Garage door repair in ${city}, FL by D &amp; B Garage Doors. Spring repair, opener repair, installation, cable repair, tune-ups, and emergency service. Call (561) 305-5853.`;
  const ogDesc = `Fast, reliable garage door repair in ${city}, FL. Spring repair, opener repair, installation, tune-ups &amp; emergency service. Call (561) 305-5853.`;
  const canonicalUrl = `https://www.dandbgaragedoors.com/locations/${citySlug}/`;

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Garage Door Repair in ${city}, FL | D &amp; B Garage Doors</title>
    <meta name="description" content="${metaDesc}" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <meta name="theme-color" content="#0A0E1A" />
    <link rel="canonical" href="${canonicalUrl}" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />

    <meta property="og:type" content="website" />
    <meta property="og:image" content="https://www.dandbgaragedoors.com/images/og-image.jpg" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:title" content="Garage Door Repair in ${city}, FL | D &amp; B Garage Doors" />
    <meta property="og:description" content="${ogDesc}" />
    <meta property="og:url" content="${canonicalUrl}" />
    <meta property="og:site_name" content="D &amp; B Garage Doors" />
    <meta property="og:locale" content="en_US" />

    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "D & B Garage Doors",
        "url": "${canonicalUrl}",
        "telephone": "+15613055853",
        "email": "service@dbgaragedoors.com",
        "areaServed": "${city}, FL",
        "address": {
          "@type": "PostalAddress",
          "addressLocality": "${city}",
          "addressRegion": "FL",
          "addressCountry": "US"
        },
        "serviceType": [
          "Spring Repair", "Opener Repair", "Installation",
          "Cable Repair", "Tune-Up", "Emergency Service"
        ]
      }
    </script>

    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": "${canonicalUrl}#breadcrumb",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.dandbgaragedoors.com/" },
          { "@type": "ListItem", "position": 2, "name": "Service Areas", "item": "https://www.dandbgaragedoors.com/#service-areas" },
          { "@type": "ListItem", "position": 3, "name": "${city}", "item": "${canonicalUrl}" }
        ]
      }
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
            <div class="text-xs text-text-muted">${city}, FL</div>
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

    <main id="main">
      <section id="top" class="relative min-h-[75vh] flex items-center overflow-hidden pt-24 pb-12" aria-label="Hero">
        <div class="pointer-events-none absolute inset-0" aria-hidden="true">
          <div class="absolute left-1/4 top-1/4 h-[350px] w-[350px] opacity-25" style="background:radial-gradient(circle,#DC2626 0%,transparent 70%);animation:blob-morph 8s ease-in-out infinite,float 12s ease-in-out infinite"></div>
          <div class="absolute right-1/4 bottom-1/4 h-[280px] w-[280px] opacity-15" style="background:radial-gradient(circle,#F87171 0%,transparent 70%);animation:blob-morph 10s ease-in-out infinite reverse,float 14s ease-in-out infinite 2s"></div>
        </div>
        <div class="pointer-events-none absolute inset-0 opacity-[0.04]" aria-hidden="true" style="background-size:60px 60px;background-image:linear-gradient(rgba(255,255,255,0.1) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.1) 1px,transparent 1px)"></div>

        <div class="relative z-10 mx-auto max-w-7xl px-6 w-full">
          <div class="grid lg:grid-cols-2 gap-10 items-center">
            <div>
              <div class="reveal inline-flex items-center gap-2 rounded-full border border-border-glass bg-surface-glass px-4 py-1.5 text-sm text-text-muted backdrop-blur-sm mb-6">
                <svg class="w-4 h-4 text-primary-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>
                Licensed &amp; Insured &bull; Same-Day Service
              </div>
              <h1 class="reveal text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.08] tracking-tight" style="transition-delay:0.1s">
                Garage Door Repair in <span class="gradient-text">${city}, FL</span>
              </h1>
              <p class="reveal mt-5 text-lg text-text-muted max-w-xl leading-relaxed" style="transition-delay:0.2s">
                Need fast help in ${city}? D &amp; B Garage Doors provides dependable repairs, installations, and emergency service. Call now for same-day scheduling.
              </p>
              <div class="reveal flex flex-wrap gap-4 mt-8" style="transition-delay:0.3s">
                <a href="tel:+15613055853" class="js-phone-link group cursor-pointer inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-primary-dark px-7 py-3.5 text-base font-semibold text-white transition-all duration-200 hover:shadow-[0_0_32px_rgba(220,38,38,0.4)]">
                  Call Now
                  <svg class="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
                <a href="/" class="cursor-pointer inline-flex items-center gap-2 rounded-full border border-border-glass bg-surface-glass px-7 py-3.5 text-base font-medium backdrop-blur-sm transition-all duration-200 hover:border-primary/30 hover:bg-white/[0.08]">
                  Back to Homepage
                </a>
              </div>
            </div>

            <div class="reveal" style="transition-delay:0.2s">
              <div class="glass-card border-primary/20 overflow-hidden shadow-2xl p-6">
                ${heroParagraphs}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="services" class="py-20 lg:py-28" aria-label="Services">
        <div class="mx-auto max-w-7xl px-6">
          <div class="reveal">
            <p class="text-sm font-medium uppercase tracking-widest text-primary-light">What We Do</p>
            <h2 class="mt-2 text-3xl sm:text-4xl font-bold tracking-tight">Our Services in ${city}</h2>
            <p class="mt-3 max-w-xl text-text-muted">Professional garage door solutions with fast response times across ${city}.</p>
          </div>
          <div class="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" role="list">
            <article class="reveal glass-card group p-6 transition-all duration-300 hover:border-primary/25 hover:bg-white/[0.06]" role="listitem" style="transition-delay:0s">
              <div class="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 text-primary-light"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M12 6v6l4 2"/></svg></div>
              <h3 class="text-lg font-semibold">Spring Repair</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-muted">Broken torsion or extension springs replaced safely with correct sizing and balance.</p>
            </article>
            <article class="reveal glass-card group p-6 transition-all duration-300 hover:border-primary/25 hover:bg-white/[0.06]" role="listitem" style="transition-delay:0.08s">
              <div class="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 text-primary-light"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M12 12h.01"/><path d="M17 12h.01"/><path d="M7 12h.01"/></svg></div>
              <h3 class="text-lg font-semibold">Opener Repair</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-muted">Remotes, sensors, gears, and motor issues diagnosed and repaired quickly.</p>
            </article>
            <article class="reveal glass-card group p-6 transition-all duration-300 hover:border-primary/25 hover:bg-white/[0.06]" role="listitem" style="transition-delay:0.16s">
              <div class="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 text-primary-light"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></div>
              <h3 class="text-lg font-semibold">Installation</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-muted">New garage doors and openers installed cleanly and tuned for smooth, quiet performance.</p>
            </article>
            <article class="reveal glass-card group p-6 transition-all duration-300 hover:border-primary/25 hover:bg-white/[0.06]" role="listitem" style="transition-delay:0.24s">
              <div class="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 text-primary-light"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg></div>
              <h3 class="text-lg font-semibold">Cable Repair</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-muted">Snapped or fraying lift cables replaced and the system rebalanced for safe movement.</p>
            </article>
            <article class="reveal glass-card group p-6 transition-all duration-300 hover:border-primary/25 hover:bg-white/[0.06]" role="listitem" style="transition-delay:0.32s">
              <div class="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 text-primary-light"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg></div>
              <h3 class="text-lg font-semibold">Tune-Up</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-muted">Inspection, lubrication, adjustments, and safety checks to reduce noise and prevent breakdowns.</p>
            </article>
            <article class="reveal glass-card group p-6 transition-all duration-300 hover:border-primary/25 hover:bg-white/[0.06]" role="listitem" style="transition-delay:0.4s">
              <div class="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary-light/10 text-primary-light"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
              <h3 class="text-lg font-semibold">Emergency Service</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-muted">Urgent situations handled fast—stuck doors, off-track rollers, or unsafe operation.</p>
            </article>
          </div>
        </div>
      </section>

      <section class="py-20 lg:py-28 border-t border-border-glass" aria-label="${city} garage door details">
        <div class="mx-auto max-w-4xl px-6">
          <div class="reveal glass-card border-primary/15 overflow-hidden p-6 sm:p-8">
            ${ctaParagraphs}
            <div class="flex flex-wrap gap-4 mt-8">
              <a href="tel:+15613055853" class="js-phone-link group cursor-pointer inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-primary-dark px-7 py-3.5 text-base font-semibold text-white transition-all duration-200 hover:shadow-[0_0_32px_rgba(220,38,38,0.4)]">
                Call (561) 305-5853
                <svg class="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
              <a href="/" class="cursor-pointer inline-flex items-center gap-2 rounded-full border border-border-glass bg-surface-glass px-7 py-3.5 text-base font-medium backdrop-blur-sm transition-all duration-200 hover:border-primary/30 hover:bg-white/[0.08]">
                Back to Homepage
              </a>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="border-t border-border-glass py-10" aria-label="Footer">
      <div class="mx-auto max-w-7xl px-6">
        <div class="flex flex-col sm:flex-row items-start justify-between gap-6">
          <div>
            <strong class="text-lg font-bold">D &amp; B Garage Doors</strong>
            <div class="mt-2 text-sm text-text-muted">Garage door repair &amp; installation in Palm Beach County, FL.</div>
            <div class="mt-1 text-sm text-text-muted">Service area: ${city} &amp; surrounding Palm Beach County cities.</div>
          </div>
          <div class="text-sm text-text-muted">
            Email: <a href="mailto:service@dbgaragedoors.com" class="cursor-pointer text-primary-light hover:text-primary transition-colors duration-200">service@dbgaragedoors.com</a>
          </div>
        </div>
        <div class="mt-6 text-xs text-text-muted">&copy; <span id="year"></span> D &amp; B Garage Doors. All rights reserved.</div>
      </div>
    </footer>

    <div class="mobile-bar" aria-label="Mobile call bar">
      <a href="tel:+15613055853" class="js-phone-link cursor-pointer flex items-center justify-center gap-2 w-full rounded-xl bg-gradient-to-r from-primary to-primary-dark py-4 text-lg font-bold text-white">
        Call Now: <span class="js-phone-display">(561) 305-5853</span>
      </a>
    </div>

    <script src="/js/main.js"></script>
  </body>
</html>`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "GET") {
      return new Response("SEO publish worker — POST /publish with Bearer AUTH_TOKEN", {
        headers: { "content-type": "text/plain;charset=UTF-8" },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, "") || "/";

    const auth = request.headers.get("Authorization") ?? "";
    const token = env.AUTH_TOKEN?.trim() ?? "";
    if (!token || auth !== `Bearer ${token}`) {
      return new Response(JSON.stringify({ ok: false, error: "unauthorized" }), {
        status: 401,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    if (path !== "/publish" && path !== "") {
      return new Response(JSON.stringify({ ok: false, error: "not_found" }), {
        status: 404,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    let body: PublishBody;
    try {
      body = (await request.json()) as PublishBody;
    } catch {
      return new Response(JSON.stringify({ ok: false, error: "invalid_json" }), {
        status: 400,
        headers: { "content-type": "application/json;charset=UTF-8" },
      });
    }

    const rawHtml = (body.html ?? "").trim();
    const markdown = (body.markdown ?? "").slice(0, 100_000);

    const city = (body.city ?? "").trim() || "Unknown City";
    const citySlug = city.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

    let htmlContent: string;
    let summaryText: string;

    if (rawHtml.length > 0) {
      htmlContent = rawHtml.slice(0, 500_000);
      const hubSlug = (body.hubSlug ?? "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-")
        .replace(/^-|-$/g, "") || "hub-page";
      const hubPrompt = [
        "You are a publishing assistant. Summarize this topical hub HTML for a reviewer.",
        "Call out risks (legal claims, wrong region, missing license). Max 6 bullets.",
        `Topic label: ${city}`,
        "",
        rawHtml.replace(/<[^>]+>/g, " ").slice(0, 12_000),
      ].join("\n");
      const summary = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
        messages: [
          { role: "system", content: "Be concise. Output plain text bullets only." },
          { role: "user", content: hubPrompt },
        ],
      });
      summaryText = typeof summary === "string" ? summary : JSON.stringify(summary);
    } else {
      if (!markdown.trim()) {
        return new Response(JSON.stringify({ ok: false, error: "markdown_required" }), {
          status: 400,
          headers: { "content-type": "application/json;charset=UTF-8" },
        });
      }

      const prompt = [
        "You are a publishing assistant. Summarize the following Markdown for a human reviewer.",
        "Call out risks (missing disclaimers, wrong city, broken tone). Max 8 bullet points.",
        `Target city: ${city}`,
        "",
        markdown.slice(0, 24_000),
      ].join("\n");

      const summary = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
        messages: [
          { role: "system", content: "Be concise. Output plain text bullets only." },
          { role: "user", content: prompt },
        ],
      });
      summaryText = typeof summary === "string" ? summary : JSON.stringify(summary);

      const paragraphs = mdParagraphsToHtml(markdown);
      htmlContent = buildLocationHtml(city, citySlug, paragraphs);
    }

    // GitHub commit
    const ghToken = env.GITHUB_TOKEN?.trim();
    const ghRepo = env.GITHUB_REPO?.trim();
    const ghBranch = env.GITHUB_BRANCH?.trim() || "main";
    let deployResult: Record<string, unknown> = { skipped: true, reason: "GITHUB_TOKEN or GITHUB_REPO not configured" };

    if (ghToken && ghRepo) {
      const hubSlugClean = (body.hubSlug ?? "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-")
        .replace(/^-|-$/g, "") || "hub-page";
      const filePath =
        body.targetPath?.trim() ||
        (rawHtml.length > 0 ? `guides/${hubSlugClean}/index.html` : `locations/${citySlug}/index.html`);
      const apiBase = `https://api.github.com/repos/${ghRepo}/contents/${filePath}`;
      const ghHeaders = {
        Authorization: `Bearer ${ghToken}`,
        "Content-Type": "application/json",
        "User-Agent": "seo-publish-worker",
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      };

      let sha: string | undefined;
      const existing = await fetch(`${apiBase}?ref=${ghBranch}`, { headers: ghHeaders });
      if (existing.ok) {
        const existingJson = (await existing.json()) as GitHubFileResponse;
        sha = existingJson.sha;
      }

      const commitPayload: Record<string, unknown> = {
        message: rawHtml.length > 0 ? `SEO hub publish: ${hubSlugClean}` : `SEO auto-publish: ${city}`,
        content: btoa(unescape(encodeURIComponent(htmlContent))),
        branch: ghBranch,
      };
      if (sha) commitPayload.sha = sha;

      const commitRes = await fetch(apiBase, { method: "PUT", headers: ghHeaders, body: JSON.stringify(commitPayload) });

      if (commitRes.ok) {
        const commitJson = (await commitRes.json()) as { commit?: { html_url?: string } };
        deployResult = { ok: true, filePath, branch: ghBranch, commitUrl: commitJson.commit?.html_url ?? null };
      } else {
        const errText = await commitRes.text();
        deployResult = { ok: false, status: commitRes.status, error: errText };
      }
    }

    return new Response(
      JSON.stringify({ ok: true, city, citySlug, summary: summaryText, deploy: deployResult }, null, 2),
      { headers: { "content-type": "application/json;charset=UTF-8" } },
    );
  },
};

interface Ai {
  run(model: string, options: { messages: { role: string; content: string }[] }): Promise<unknown>;
}
