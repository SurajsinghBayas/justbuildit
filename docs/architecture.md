# justbuildit — Architecture Overview

## System Design

```
                        ┌──────────────┐
                        │   Users      │
                        └──────┬───────┘
                               │ HTTPS
                        ┌──────▼───────┐
                        │   Nginx      │ (reverse proxy)
                        └──┬───┬───┬───┘
                           │   │   │
              ┌────────────┘   │   └─────────────┐
              │                │                 │
       ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
       │  Frontend   │  │   Backend   │  │ AI Service  │
       │  Next.js    │  │  FastAPI    │  │  FastAPI +  │
       │  (Vercel)   │  │  (AWS EC2)  │  │  scikit-learn│
       └─────────────┘  └──────┬──────┘  └─────────────┘
                               │
              ┌────────────────┴──────────────────┐
              │                                   │
       ┌──────▼──────┐                   ┌────────▼──────┐
       │ PostgreSQL  │                   │    Redis      │
       │  (AWS RDS)  │                   │ (ElastiCache) │
       └─────────────┘                   └───────────────┘
```

## Components

| Component   | Technology                | Hosting           |
|-------------|---------------------------|-------------------|
| Frontend    | Next.js 14, TypeScript    | Vercel            |
| Backend API | FastAPI, SQLAlchemy       | AWS EC2 / ECS     |
| AI Service  | FastAPI, scikit-learn     | AWS EC2           |
| Database    | PostgreSQL 16             | AWS RDS           |
| Cache/Queue | Redis 7                   | AWS ElastiCache   |
| CDN / Files | S3 + CloudFront           | AWS               |
| CI/CD       | GitHub Actions            | GitHub            |

## Design Decisions

### ADR-001: Async-first Backend
**Decision**: Use `asyncpg` + `SQLAlchemy async` for all DB interactions.  
**Rationale**: Handles concurrent requests efficiently without thread-pool exhaustion.

### ADR-002: Service Separation
**Decision**: AI microservice is separate from the main backend.  
**Rationale**: Independent scaling, Python-only ML dependencies don't pollute backend.

### ADR-003: JWT over Sessions
**Decision**: Stateless JWT tokens (access + refresh).  
**Rationale**: Supports multiple frontend clients (web, mobile) without server-side session storage.

### ADR-004: Celery for Background Jobs
**Decision**: Celery + Redis for async tasks.  
**Rationale**: GitHub sync and reminders should not block HTTP request/response cycles.

## Data Flow — Task Creation

1. User creates task in frontend
2. `POST /api/v1/tasks` → Backend validates, persists to PostgreSQL
3. Celery task `recalculate_project_progress` triggered
4. Frontend calls `POST /ai/recommend/priority` → AI Service returns suggested priority
5. Task visible in Kanban board via React state update
