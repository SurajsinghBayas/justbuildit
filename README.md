# justbuildit 🚀

> AI-powered project and task management platform.

## Architecture

```
justbuildit/
├── frontend/       # Next.js 13+ App Router (Vercel)
├── backend/        # FastAPI + Celery (AWS EC2 / ECS)
├── ai-service/     # ML microservice (FastAPI + scikit-learn)
├── infra/          # Docker, Terraform, GitHub Actions
├── docs/           # Architecture & API documentation
└── scripts/        # Dev utilities
```

## Quick Start (Local)

```bash
cp .env.example .env
docker compose up --build
```

| Service      | URL                      |
|--------------|--------------------------|
| Frontend     | http://localhost:3000    |
| Backend API  | http://localhost:8000    |
| AI Service   | http://localhost:8001    |
| API Docs     | http://localhost:8000/docs |

## Tech Stack

| Layer        | Technology                              |
|--------------|-----------------------------------------|
| Frontend     | Next.js 13, TypeScript, Zustand, Tailwind CSS |
| Backend      | FastAPI, SQLAlchemy, Alembic, Celery    |
| AI           | FastAPI, scikit-learn, pandas, joblib   |
| Database     | PostgreSQL                              |
| Cache/Queue  | Redis                                   |
| Auth         | JWT + Google OAuth2                     |
| Infra        | Docker, Terraform (AWS), GitHub Actions |

## Environment Variables

See `.env.example` for all required variables.

## Docs

- [Architecture](docs/architecture.md)
- [API Spec](docs/api-spec.md)
- [DB Schema](docs/db-schema.md)
- [AI Model](docs/ai-model.md)

## Development

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# AI Service
cd ai-service && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
