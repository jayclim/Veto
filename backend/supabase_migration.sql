-- Supabase Migration: Create tables for the Veto budgeting app
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)

-- ── User table ──────────────────────────────────────────────────
-- Note: "user" is a reserved word in PostgreSQL, so we quote it
CREATE TABLE IF NOT EXISTS "user" (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username);

-- ── Transaction table ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transaction (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES "user" (id),
    amount FLOAT8 NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Uncategorized',
    transaction_type TEXT NOT NULL DEFAULT 'expense',
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transaction_user_id ON transaction (user_id);

-- ── Budget Category table ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS budget_category (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES "user" (id),
    name TEXT NOT NULL,
    monthly_limit FLOAT8 NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_budget_category_user_id ON budget_category (user_id);

-- ── Budget Rule table ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budget_rule (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES "user" (id),
    rule_type TEXT NOT NULL,
    name TEXT NOT NULL,
    config TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_budget_rule_user_id ON budget_rule (user_id);

-- ── Row Level Security (optional but recommended) ───────────────
-- Enable RLS on all tables
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_category ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_rule ENABLE ROW LEVEL SECURITY;

-- Allow the service role (used by backend) full access
CREATE POLICY "Service role full access" ON "user"
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON transaction
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON budget_category
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON budget_rule
    FOR ALL USING (true) WITH CHECK (true);
