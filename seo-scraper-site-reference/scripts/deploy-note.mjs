console.log(`
  ──────────────────────────────────────────────────
  Deploy finished.

  Your real site (after Custom domain + DNS in Cloudflare):
    https://www.dandbgaragedoors.com

  Cloudflare also assigns this Pages project a built-in hostname
  (see the *.pages.dev link a few lines UP in Wrangler’s output).
  That is the same deployment—not a separate “dev server” you manage.

  If live /get-blogs errors with no such column: published:
    npm run d1:describe-blog_posts:remote   # confirm columns on CLI-bound DB
    npm run d1:fix-published:remote        # ALTER TABLE (or duplicate-column → binding mismatch)
    npm run verify:get-blogs               # curl-style check /get-blogs
    Dashboard → Pages → db-garage-doors → Functions → D1 binding UUID must match npx wrangler d1 info garage-db

  If the blog API is empty, articles 404, or D1 errors on slug column:
    cd seo-scraper-site-reference
    npm run d1:reset-blog-schema:remote   # once if legacy table (wipes blog rows)
    npm run d1:seed:remote               # loads 7 starter articles

  Fresh database only:
    npm run d1:migrate:remote && npm run d1:seed:remote

  Cloudflare Dashboard → Pages → db-garage-doors → Settings → Functions:
    bind D1 database "garage-db" as DB (must match wrangler.toml).

  Regenerate seed SQL after editing scripts/build-blog-seed-sql.mjs:
    npm run d1:build-seed

  Health check:       npm run check:live
  ──────────────────────────────────────────────────
`);
