-- One-time fix: older blog_posts tables had no slug/excerpt columns.
-- Drops the table and recreates the current schema — all existing blog rows are deleted.
DROP INDEX IF EXISTS idx_blog_posts_slug;
DROP INDEX IF EXISTS idx_blog_posts_created;
DROP TABLE IF EXISTS blog_posts;

CREATE TABLE blog_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  city TEXT,
  title TEXT NOT NULL,
  excerpt TEXT,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  published INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_blog_posts_created ON blog_posts (created_at);
