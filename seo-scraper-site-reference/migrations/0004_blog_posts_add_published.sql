-- Production Pages `/get-blogs` expects column published (1 = visible, 0 = draft).
-- Run once if you seeded before published existed; skip if you already see duplicate-column errors.
ALTER TABLE blog_posts ADD COLUMN published INTEGER NOT NULL DEFAULT 1;
