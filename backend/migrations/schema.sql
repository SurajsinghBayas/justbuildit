-- ═══════════════════════════════════════════════════════════════════════════════
-- JustBuildIt — PostgreSQL Schema (Neon)
-- Multi-tenant project management with RBAC, GitHub, AI/ML, and analytics
-- ═══════════════════════════════════════════════════════════════════════════════

-- ── Extensions ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── ENUM Types ────────────────────────────────────────────────────────────────
DO $$ BEGIN
  CREATE TYPE membership_role   AS ENUM ('OWNER', 'LEADER', 'MEMBER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE project_status    AS ENUM ('ACTIVE', 'COMPLETED', 'ON_HOLD', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE task_status       AS ENUM ('TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE', 'BLOCKED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE task_priority     AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE activity_entity   AS ENUM ('TASK', 'PROJECT', 'COMMENT', 'MEMBER', 'INTEGRATION');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ══════════════════════════════════════════════════════════════════════════════
-- 👤 USERS
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email           TEXT NOT NULL UNIQUE,
  password_hash   TEXT,                         -- null for OAuth-only users
  name            TEXT NOT NULL,
  avatar_url      TEXT,
  google_id       TEXT UNIQUE,
  github_id       TEXT UNIQUE,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
  is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 🏢 ORGANIZATIONS (Tenants)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS organizations (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,
  logo_url    TEXT,
  owner_id    UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 🤝 MEMBERSHIPS (RBAC — tenant isolation join table)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS memberships (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role            membership_role NOT NULL DEFAULT 'MEMBER',
  joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, organization_id)
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 📁 PROJECTS
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS projects (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  description     TEXT,
  status          project_status NOT NULL DEFAULT 'ACTIVE',
  created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- ✅ TASKS (Kanban-ready via task_status enum)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS tasks (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,  -- tenant isolation
  assigned_to     UUID REFERENCES users(id) ON DELETE SET NULL,
  created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  title           TEXT NOT NULL,
  description     TEXT,
  status          task_status NOT NULL DEFAULT 'TODO',
  priority        task_priority NOT NULL DEFAULT 'MEDIUM',
  deadline        TIMESTAMPTZ,
  estimated_time  NUMERIC(6, 2),               -- in hours
  actual_time     NUMERIC(6, 2),               -- in hours (filled on completion)
  tags            TEXT[] DEFAULT '{}',
  github_issue_number INT,
  is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 💬 COMMENTS
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS comments (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content         TEXT NOT NULL,
  is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 📜 ACTIVITY LOGS (Audit trail)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS activity_logs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id         UUID REFERENCES users(id) ON DELETE SET NULL,  -- null = system action
  action          TEXT NOT NULL,                                  -- e.g. "task.status_changed"
  entity_type     activity_entity NOT NULL,
  entity_id       UUID NOT NULL,
  metadata        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
  -- Intentionally no is_deleted — logs are immutable
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 🔗 GITHUB INTEGRATIONS
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS github_integrations (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id      UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  repo_name       TEXT NOT NULL,
  repo_url        TEXT NOT NULL,
  access_token    TEXT,              -- store encrypted at app layer
  webhook_secret  TEXT,
  github_app_id   TEXT,
  installation_id BIGINT,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 🐙 GITHUB EVENTS (Commits, PRs, Issues)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS github_events (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  integration_id  UUID NOT NULL REFERENCES github_integrations(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  event_type      TEXT NOT NULL,          -- 'push', 'pull_request', 'issues'
  payload         JSONB NOT NULL DEFAULT '{}',
  sha             TEXT,                   -- commit SHA if applicable
  pr_number       INT,
  branch          TEXT,
  author          TEXT,
  message         TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 📊 ANALYTICS SNAPSHOTS (point-in-time metrics per project)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS analytics_snapshots (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  tasks_total         INT NOT NULL DEFAULT 0,
  tasks_completed     INT NOT NULL DEFAULT 0,
  tasks_pending       INT NOT NULL DEFAULT 0,
  tasks_blocked       INT NOT NULL DEFAULT 0,
  velocity_score      NUMERIC(6, 2),      -- tasks completed per sprint
  avg_completion_time NUMERIC(8, 4),      -- average hours to complete a task
  on_time_rate        NUMERIC(5, 4),      -- ratio 0.0–1.0
  recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- 🤖 AI PREDICTIONS (delay risk per task)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_predictions (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  task_id             UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  predicted_delay     BOOLEAN NOT NULL,
  confidence_score    NUMERIC(5, 4) NOT NULL,   -- 0.0000 – 1.0000
  model_version       TEXT,
  features_snapshot   JSONB DEFAULT '{}',        -- input features used for prediction
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ════════════════════════════════════════════════════════════════════════════════
-- ⚡ INDEXES
-- ════════════════════════════════════════════════════════════════════════════════

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email       ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id   ON users(google_id) WHERE google_id IS NOT NULL;

-- Memberships (tenant RBAC lookup)
CREATE INDEX IF NOT EXISTS idx_memberships_user_org ON memberships(user_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_memberships_org      ON memberships(organization_id);

-- Projects
CREATE INDEX IF NOT EXISTS idx_projects_org_id    ON projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_projects_status    ON projects(organization_id, status);

-- Tasks (most queried table)
CREATE INDEX IF NOT EXISTS idx_tasks_project_id   ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_org_id       ON tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to  ON tasks(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_status       ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline     ON tasks(deadline) WHERE deadline IS NOT NULL AND is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_tasks_tags         ON tasks USING GIN(tags);

-- Comments
CREATE INDEX IF NOT EXISTS idx_comments_task_id   ON comments(task_id);
CREATE INDEX IF NOT EXISTS idx_comments_org_id    ON comments(organization_id);

-- Activity logs
CREATE INDEX IF NOT EXISTS idx_activity_org_id    ON activity_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_entity    ON activity_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activity_user_id   ON activity_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_metadata  ON activity_logs USING GIN(metadata);

-- GitHub integrations
CREATE INDEX IF NOT EXISTS idx_github_integrations_project ON github_integrations(project_id);
CREATE INDEX IF NOT EXISTS idx_github_integrations_org     ON github_integrations(organization_id);

-- GitHub events
CREATE INDEX IF NOT EXISTS idx_github_events_integration ON github_events(integration_id);
CREATE INDEX IF NOT EXISTS idx_github_events_type        ON github_events(event_type);
CREATE INDEX IF NOT EXISTS idx_github_events_payload     ON github_events USING GIN(payload);

-- Analytics
CREATE INDEX IF NOT EXISTS idx_analytics_project_time ON analytics_snapshots(project_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_org_id       ON analytics_snapshots(organization_id);

-- AI Predictions
CREATE INDEX IF NOT EXISTS idx_ai_predictions_task ON ai_predictions(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_org  ON ai_predictions(organization_id);


-- ════════════════════════════════════════════════════════════════════════════════
-- 🔄 updated_at auto-update trigger
-- ════════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER set_users_updated_at
  BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_organizations_updated_at
  BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_projects_updated_at
  BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_tasks_updated_at
  BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_comments_updated_at
  BEFORE UPDATE ON comments FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE TRIGGER set_github_integrations_updated_at
  BEFORE UPDATE ON github_integrations FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
