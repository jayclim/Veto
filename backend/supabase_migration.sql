-- Supabase Migration: Create tables for the Veto budgeting app
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)

-- ── User table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS veto_users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_veto_users_username ON veto_users (username);

-- ── Transaction table ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS veto_transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES veto_users (id),
    amount FLOAT8 NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Uncategorized',
    transaction_type TEXT NOT NULL DEFAULT 'expense',
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_veto_transactions_user_id ON veto_transactions (user_id);

-- ── Budget Rule table ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS veto_budget_rules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES veto_users (id),
    rule_type TEXT NOT NULL,
    name TEXT NOT NULL,
    config TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_veto_budget_rules_user_id ON veto_budget_rules (user_id);

-- ── Row Level Security (optional but recommended) ───────────────
-- Enable RLS on all tables
ALTER TABLE veto_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE veto_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE veto_budget_rules ENABLE ROW LEVEL SECURITY;

-- Allow the service role (used by backend) full access
CREATE POLICY "Service role full access" ON veto_users
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON veto_transactions
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON veto_budget_rules
    FOR ALL USING (true) WITH CHECK (true);
