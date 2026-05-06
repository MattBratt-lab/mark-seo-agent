-- D1 schema for /get-blogs and dynamic /blog/:slug pages.
-- If migrate fails or seed says "no such column: slug", your DB has a legacy table —
-- run once: npm run d1:reset-blog-schema:remote
CREATE TABLE IF NOT EXISTS blog_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  city TEXT,
  title TEXT NOT NULL,
  excerpt TEXT,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  published INTEGER NOT NULL DEFAULT 1
);

-- Avoid CREATE INDEX on slug here: legacy tables lack slug and would error.
-- slug already has an implicit unique index when this CREATE TABLE runs on a new DB.
CREATE INDEX IF NOT EXISTS idx_blog_posts_created ON blog_posts (created_at);
