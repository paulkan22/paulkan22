CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_category TEXT,
    monitor_group_count INTEGER NOT NULL DEFAULT 0,
    mutual_reference_count INTEGER NOT NULL DEFAULT 0,
    mutual_groups_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_mutual_check TIMESTAMPTZ,
    source_chat TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_first_seen ON users(first_seen);
CREATE INDEX IF NOT EXISTS idx_users_mutual_reference_count ON users(mutual_reference_count);

CREATE TABLE IF NOT EXISTS groups (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT UNIQUE NOT NULL,
    title TEXT,
    type TEXT NOT NULL CHECK (type IN ('reference', 'monitor')),
    status TEXT,
    cluster_id INTEGER,
    last_checked TIMESTAMPTZ,
    last_scraped TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_groups_type ON groups(type);
CREATE INDEX IF NOT EXISTS idx_groups_cluster_id ON groups(cluster_id);

CREATE TABLE IF NOT EXISTS accounts (
    id BIGSERIAL PRIMARY KEY,
    session_path TEXT NOT NULL,
    api_id BIGINT NOT NULL DEFAULT 0,
    api_hash TEXT NOT NULL DEFAULT '',
    proxy TEXT,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'COOLDOWN', 'SLEEP', 'ERROR')),
    dynamic_limit INTEGER NOT NULL DEFAULT 80,
    trust_score INTEGER NOT NULL DEFAULT 0,
    sleep_until TIMESTAMPTZ,
    cluster_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
CREATE INDEX IF NOT EXISTS idx_accounts_cluster_id ON accounts(cluster_id);

CREATE TABLE IF NOT EXISTS mutual_tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    next_try_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL,
    cluster_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_mutual_tasks_user_id ON mutual_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_mutual_tasks_status ON mutual_tasks(status);
CREATE INDEX IF NOT EXISTS idx_mutual_tasks_next_try_at ON mutual_tasks(next_try_at);


CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_user_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_user_id ON audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

CREATE TABLE IF NOT EXISTS backup_runs (
    id BIGSERIAL PRIMARY KEY,
    status TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backup_runs_created_at ON backup_runs(created_at);
