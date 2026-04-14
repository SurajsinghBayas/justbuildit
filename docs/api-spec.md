# justbuildit — API Specification

Base URL: `https://api.justbuildit.app/api/v1`

## Authentication

All endpoints (except `/auth/login` and `/auth/register`) require:
```
Authorization: Bearer <access_token>
```

---

## Auth

| Method | Endpoint              | Description            |
|--------|-----------------------|------------------------|
| POST   | `/auth/register`      | Register new user      |
| POST   | `/auth/login`         | Login, get tokens      |
| POST   | `/auth/refresh`       | Refresh access token   |
| GET    | `/auth/me`            | Get current user       |
| POST   | `/auth/logout`        | Invalidate tokens      |

### POST /auth/login
```json
// Request
{ "email": "user@example.com", "password": "secret123" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Projects

| Method | Endpoint              | Description             |
|--------|-----------------------|-------------------------|
| GET    | `/projects`           | List user's projects    |
| POST   | `/projects`           | Create project          |
| GET    | `/projects/{id}`      | Get project             |
| PUT    | `/projects/{id}`      | Update project          |
| DELETE | `/projects/{id}`      | Delete project          |

---

## Tasks

| Method | Endpoint                    | Description               |
|--------|-----------------------------|---------------------------|
| GET    | `/tasks?project_id={id}`    | List tasks (filterable)   |
| POST   | `/tasks`                    | Create task               |
| GET    | `/tasks/{id}`               | Get task                  |
| PUT    | `/tasks/{id}`               | Update task               |
| PATCH  | `/tasks/{id}/status`        | Update task status only   |
| DELETE | `/tasks/{id}`               | Delete task               |

### PATCH /tasks/{id}/status
```json
// Request
{ "status": "in_progress" }
// Valid statuses: todo | in_progress | in_review | done | blocked
```

---

## Analytics

| Method | Endpoint                | Description               |
|--------|-------------------------|---------------------------|
| GET    | `/analytics/summary`    | Task distribution summary |
| GET    | `/analytics/velocity`   | Sprint velocity data      |

---

## GitHub

| Method | Endpoint           | Description                    |
|--------|--------------------|--------------------------------|
| POST   | `/github/webhook`  | Receive GitHub webhook events  |

---

## AI Service (port 8001)

| Method | Endpoint               | Description                      |
|--------|------------------------|----------------------------------|
| POST   | `/predict/delay`       | Predict if a task will be delayed|
| POST   | `/recommend/assignee`  | Recommend task assignee          |
| POST   | `/recommend/priority`  | Suggest task priority            |

### POST /predict/delay
```json
// Request
{
  "task_id": "abc-123",
  "complexity": 4.0,
  "assignee_load": 12,
  "days_remaining": 2,
  "open_blockers": 1,
  "team_velocity": 8.0
}

// Response
{
  "task_id": "abc-123",
  "will_delay": true,
  "probability": 0.82,
  "confidence": 0.64
}
```
