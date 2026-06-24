-- ============================================================
-- AusTap — Supabase Database Setup
-- Run this entire file in the Supabase SQL Editor
-- ============================================================

-- 1. Businesses table
CREATE TABLE IF NOT EXISTS businesses (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL,
  slug         TEXT NOT NULL UNIQUE,
  redirect_url TEXT NOT NULL,
  platform     TEXT NOT NULL CHECK (platform IN ('google', 'yelp', 'tripadvisor')),
  owner_email  TEXT,
  active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Taps table
CREATE TABLE IF NOT EXISTS taps (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id  UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  tapped_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  device_type  TEXT,
  city         TEXT
);

-- 3. Index for fast tap lookups by business and date
CREATE INDEX IF NOT EXISTS idx_taps_business_tapped ON taps (business_id, tapped_at DESC);

-- 4. Seed: two example businesses for testing
INSERT INTO businesses (name, slug, redirect_url, platform, owner_email, active)
VALUES
  (
    'Demo Coffee Shop',
    'demo-coffee',
    'https://g.page/r/REPLACE_WITH_REAL_GOOGLE_REVIEW_LINK/review',
    'google',
    'demo@example.com',
    TRUE
  ),
  (
    'Demo Hair Salon',
    'demo-salon',
    'https://g.page/r/REPLACE_WITH_REAL_GOOGLE_REVIEW_LINK/review',
    'google',
    'salon@example.com',
    TRUE
  )
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- Done! You should see the businesses table populated above.
-- Update the redirect_url values with your real Google review links.
-- ============================================================
