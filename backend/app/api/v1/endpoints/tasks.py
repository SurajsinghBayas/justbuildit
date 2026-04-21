from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate, TaskStatusUpdate
from app.services.task_service import TaskService

router = APIRouter()


async def _resolve_org_for_project(db: AsyncSession, project_id: str, user_id: str) -> str:
    """Return the organization_id for the given project, falling back to user's first org."""
    from app.models.project import Project
    from sqlalchemy import select
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        return project.organization_id
    from app.services.organization_service import OrganizationService
    org_svc = OrganizationService(db)
    orgs = await org_svc.list_for_user(user_id)
    if not orgs:
        raise HTTPException(status_code=400, detail="Cannot determine organization for task")
    return orgs[0].id


@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = TaskService(db)
    return await svc.list(user_id=user_id, project_id=project_id)


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = TaskService(db)
    payload.created_by = user_id
    if not payload.organization_id:
        payload.organization_id = await _resolve_org_for_project(db, payload.project_id, user_id)
    return await svc.create(payload)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = TaskService(db)
    task = await svc.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = TaskService(db)
    return await svc.update(task_id, payload)


@router.patch("/{task_id}/status", response_model=TaskOut)
async def update_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = TaskService(db)
    return await svc.update_status(task_id, payload.status)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = TaskService(db)
    await svc.delete(task_id)


# ── AI Task Generation (AWS Bedrock — Nova Micro) ──────────────────────────────

class AIGenerateRequest(BaseModel):
    project_name: str
    project_description: Optional[str] = None
    count: int = 5


class AIGeneratedTask(BaseModel):
    title: str
    description: str
    priority: str           # LOW | MEDIUM | HIGH | CRITICAL
    estimated_time: Optional[float] = None  # hours


class AIGenerateResponse(BaseModel):
    tasks: List[AIGeneratedTask]


# Smart mock fallback — used when credentials are missing or Bedrock call fails
_MOCK_TASKS = [
    {"title": "Set up project repository and CI/CD pipeline",   "description": "Initialize Git repo, configure GitHub Actions for automated testing and deployment pipelines.",        "priority": "HIGH",     "estimated_time": 4.0},
    {"title": "Design system architecture and database schema",  "description": "Define ERD, API contracts, and service boundaries. Document architectural decisions and trade-offs.", "priority": "HIGH",     "estimated_time": 8.0},
    {"title": "Implement core authentication flow",              "description": "Build login, registration, and JWT token management with refresh tokens and secure storage.",          "priority": "HIGH",     "estimated_time": 6.0},
    {"title": "Build primary dashboard UI",                     "description": "Design and implement the main user dashboard with key metrics, charts, and navigation.",               "priority": "MEDIUM",   "estimated_time": 5.0},
    {"title": "Write unit and integration tests",                "description": "Achieve 80% code coverage for all critical paths, services, and API endpoints.",                       "priority": "MEDIUM",   "estimated_time": 6.0},
    {"title": "Set up monitoring and error tracking",            "description": "Integrate Sentry for error tracking and configure uptime monitoring with alert notifications.",         "priority": "LOW",      "estimated_time": 2.0},
    {"title": "Write API documentation and README",              "description": "Produce comprehensive API docs using OpenAPI, plus a developer setup guide and README.",               "priority": "LOW",      "estimated_time": 3.0},
    {"title": "Configure deployment infrastructure",             "description": "Set up Docker containers, Kubernetes manifests or cloud deployment scripts for production.",           "priority": "CRITICAL", "estimated_time": 10.0},
    {"title": "Implement role-based access control",            "description": "Define user roles and permissions; guard all sensitive API endpoints with proper authorization.",        "priority": "CRITICAL", "estimated_time": 7.0},
    {"title": "Conduct security audit and penetration testing",  "description": "Review code for OWASP Top 10 vulnerabilities and run automated security scans before launch.",         "priority": "HIGH",     "estimated_time": 5.0},
]


def _build_bedrock_prompt(project_name: str, description: str, count: int) -> str:
    return f"""You are a senior software project manager. Generate exactly {count} actionable tasks for the project below.

Project Name: {project_name}
Project Description: {description}

Respond with ONLY a valid JSON array (no markdown, no commentary, no code fences), containing exactly {count} objects.
Each object must have these exact keys:
- "title": string (concise action phrase, starts with a verb, max 10 words)
- "description": string (2-3 sentences, specific to this project)
- "priority": exactly one of "LOW", "MEDIUM", "HIGH", "CRITICAL"
- "estimated_time": float (realistic estimate in hours)

Priority distribution: 1-2 CRITICAL, 2-3 HIGH, 2-3 MEDIUM, 1-2 LOW.
Cover phases: project setup, core feature development, testing, and deployment."""


@router.post("/ai-generate", response_model=AIGenerateResponse)
async def ai_generate_tasks(
    payload: AIGenerateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Generate tasks using AWS Bedrock (Amazon Nova Micro via APAC inference profile)."""
    import json, re, asyncio, logging
    from concurrent.futures import ThreadPoolExecutor
    from app.core.config import settings

    log = logging.getLogger("app.ai")

    # Read from pydantic-settings (NOT os.getenv — pydantic loads .env at startup)
    aws_key    = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    aws_region = settings.AWS_DEFAULT_REGION or "ap-south-1"
    model_id   = settings.BEDROCK_MODEL_ID

    log.info(f"AI generate — key_id='{aws_key[:12]}...' region='{aws_region}' model='{model_id[:40]}...'")

    # No credentials → smart mock
    if not aws_key or not aws_secret:
        log.warning("AWS credentials not configured — returning mock tasks")
        count = min(payload.count, len(_MOCK_TASKS))
        return AIGenerateResponse(tasks=[AIGeneratedTask(**t) for t in _MOCK_TASKS[:count]])

    prompt = _build_bedrock_prompt(
        payload.project_name,
        payload.project_description or "No description provided.",
        payload.count,
    )

    def _call_bedrock() -> str:
        """Run synchronous boto3 call in a thread pool — keeps the async loop unblocked."""
        import boto3
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
        )
        resp = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 0.7,
                "topP": 0.9,
                "stopSequences": [],
            },
            additionalModelRequestFields={},
        )
        return resp["output"]["message"]["content"][0]["text"]

    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as pool:
            raw_text = await loop.run_in_executor(pool, _call_bedrock)

        log.info(f"Bedrock raw response length: {len(raw_text)}")

        # Strip any markdown code fences ```json ... ```
        clean = re.sub(r"```(?:json)?", "", raw_text).strip().rstrip("`").strip()

        # Extract the JSON array robustly (handles surrounding text)
        array_match = re.search(r"\[.*\]", clean, re.DOTALL)
        if not array_match:
            raise ValueError(f"No JSON array in response: {clean[:200]}")

        tasks_raw = json.loads(array_match.group())

        # Sanitise priority values
        valid_priorities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for t in tasks_raw:
            if t.get("priority") not in valid_priorities:
                t["priority"] = "MEDIUM"
            # Ensure estimated_time is a float
            if "estimated_time" in t:
                try:
                    t["estimated_time"] = float(t["estimated_time"])
                except (TypeError, ValueError):
                    t["estimated_time"] = 4.0

        tasks = [AIGeneratedTask(**t) for t in tasks_raw[:payload.count]]
        log.info(f"Bedrock returned {len(tasks)} tasks for project '{payload.project_name}'")
        return AIGenerateResponse(tasks=tasks)

    except Exception as exc:
        log.error(f"Bedrock AI generation failed: {exc}", exc_info=True)
        # Surface the real error so it can be debugged
        raise HTTPException(status_code=500, detail=f"Bedrock AI generation failed: {str(exc)}")
