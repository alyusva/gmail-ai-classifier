-- ============================================================
-- MIGRACIÓN 002: Multi-usuario + RLS + gmail_tokens + subscriptions
-- ============================================================

ALTER TABLE emails          ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE classifications ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE taxonomy        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE progress        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_emails_user_id           ON emails(user_id);
CREATE INDEX IF NOT EXISTS idx_classifications_user_id  ON classifications(user_id);
CREATE INDEX IF NOT EXISTS idx_taxonomy_user_id         ON taxonomy(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_user_id         ON progress(user_id);

CREATE TABLE IF NOT EXISTS gmail_tokens (
    user_id       UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    token_data    TEXT NOT NULL,
    scopes        TEXT[],
    email         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_customer_id  TEXT UNIQUE,
    stripe_sub_id       TEXT UNIQUE,
    plan                TEXT NOT NULL DEFAULT 'free',
    status              TEXT NOT NULL DEFAULT 'active',
    emails_limit        INTEGER DEFAULT 1000,
    emails_used         INTEGER DEFAULT 0,
    period_start        TIMESTAMPTZ,
    period_end          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO profiles (id, full_name, avatar_url)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'avatar_url')
    ON CONFLICT (id) DO NOTHING;
    INSERT INTO subscriptions (user_id, plan, status, emails_limit)
    VALUES (NEW.id, 'free', 'active', 1000)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

ALTER TABLE emails          ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE taxonomy        ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress        ENABLE ROW LEVEL SECURITY;
ALTER TABLE gmail_tokens    ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles        ENABLE ROW LEVEL SECURITY;

CREATE POLICY "emails_own"           ON emails           FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "classifications_own"  ON classifications  FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "taxonomy_own"         ON taxonomy         FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "progress_own"         ON progress         FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "gmail_tokens_own"     ON gmail_tokens     FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "subscriptions_own"    ON subscriptions    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "profiles_own"         ON profiles         FOR ALL USING (auth.uid() = id);

DROP VIEW IF EXISTS classification_summary;
CREATE OR REPLACE VIEW classification_summary AS
SELECT user_id, label, COUNT(*) AS email_count
FROM (SELECT user_id, UNNEST(labels) AS label FROM classifications) sub
GROUP BY user_id, label
ORDER BY email_count DESC;
