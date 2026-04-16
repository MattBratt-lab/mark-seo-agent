console.log(`
  ──────────────────────────────────────────────────
  Deploy finished.

  Your real site (after Custom domain + DNS in Cloudflare):
    https://www.dandbgaragedoors.com

  Cloudflare also assigns this Pages project a built-in hostname
  (see the *.pages.dev link a few lines UP in Wrangler’s output).
  That is the same deployment—not a separate “dev server” you manage.

  If the blog is empty: npm run d1:seed:remote
  Health check:       npm run check:live
  ──────────────────────────────────────────────────
`);
