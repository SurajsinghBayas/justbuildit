#!/usr/bin/env bash
# run_dev.sh — Start all justbuildit services for local development
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "🚀 Starting justbuildit dev environment..."
echo "   Root: $ROOT"

# ── Check prerequisites ──────────────────────────────────────────────────────
command -v docker compose >/dev/null 2>&1 || { echo "❌ docker compose not found"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ node not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found"; exit 1; }

# ── Copy .env if not exists ──────────────────────────────────────────────────
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "✅ Created .env from .env.example — please update secrets"
fi

# ── Start infra (Postgres + Redis) ───────────────────────────────────────────
echo "⏳ Starting PostgreSQL and Redis..."
docker compose -f "$ROOT/docker-compose.yml" up -d postgres redis
echo "✅ Database and Redis running"

# ── Wait for Postgres ─────────────────────────────────────────────────────────
echo "⏳ Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U postgres; do
  sleep 1
done
echo "✅ PostgreSQL ready"

# ── Run Alembic migrations ────────────────────────────────────────────────────
echo "⏳ Running database migrations..."
(cd "$ROOT/backend" && alembic upgrade head)
echo "✅ Migrations applied"

# ── Start Backend in background ───────────────────────────────────────────────
echo "⏳ Starting FastAPI backend on :8002..."
(cd "$ROOT/backend" && uvicorn app.main:app --reload --port 8002) &
BACKEND_PID=$!

# ── Start AI Service in background ───────────────────────────────────────────
echo "⏳ Starting AI service on :8001..."
(cd "$ROOT/ai-service" && uvicorn app.main:app --reload --port 8001) &
AI_PID=$!

# ── Start Frontend ────────────────────────────────────────────────────────────
echo "⏳ Installing frontend dependencies..."
(cd "$ROOT/frontend" && npm install --silent)
echo "⏳ Starting Next.js frontend on :3000..."
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════════"
echo " ⚡ justbuildit is running!"
echo "   Frontend  → http://localhost:3000"
echo "   Backend   → http://localhost:8002"
echo "   API Docs  → http://localhost:8002/api/v1/docs"
echo "   AI Service→ http://localhost:8001/docs"
echo "═══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all services"

# ── Wait and clean up ─────────────────────────────────────────────────────────
trap "echo '🛑 Shutting down...'; kill $BACKEND_PID $AI_PID $FRONTEND_PID 2>/dev/null; docker compose stop postgres redis" INT
wait
