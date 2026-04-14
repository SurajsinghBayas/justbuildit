# justbuildit — Database Schema

## ERD (simplified)

```
users ──────────────────────────────────────────────────────────
  id (PK, uuid)
  name (varchar 255)
  email (varchar 320, unique)
  hashed_password (varchar, nullable)
  avatar_url (varchar, nullable)
  google_id (varchar, unique, nullable)
  github_id (varchar, unique, nullable)
  is_active (bool, default true)
  is_superuser (bool, default false)
  created_at / updated_at

organizations ───────────────────────────────────────────────────
  id (PK, uuid)
  name (varchar 255)
  slug (varchar 100, unique)
  logo_url (varchar, nullable)
  owner_id (FK → users.id)
  created_at / updated_at

memberships ─────────────────────────────────────────────────────
  id (PK, uuid)
  user_id (FK → users.id)
  organization_id (FK → organizations.id)
  role (varchar 50) — admin | member | viewer
  joined_at
  UNIQUE(user_id, organization_id)

projects ────────────────────────────────────────────────────────
  id (PK, uuid)
  name (varchar 255)
  description (text, nullable)
  status (varchar 50) — active | paused | archived
  progress (float, 0-100)
  organization_id (FK → organizations.id)
  owner_id (FK → users.id)
  github_repo (varchar, nullable)
  created_at / updated_at

tasks ───────────────────────────────────────────────────────────
  id (PK, uuid)
  title (varchar 512)
  description (text, nullable)
  status (varchar 50) — todo | in_progress | in_review | done | blocked
  priority (varchar 50) — low | medium | high | critical
  project_id (FK → projects.id)
  assignee_id (FK → users.id, nullable)
  due_date (timestamptz, nullable)
  github_issue_number (int, nullable)
  created_at / updated_at
```

## Indexes

| Table    | Columns                     | Type   |
|----------|-----------------------------|--------|
| users    | email                       | UNIQUE |
| tasks    | project_id                  | BTREE  |
| tasks    | status                      | BTREE  |
| memberships | (user_id, organization_id) | UNIQUE |
