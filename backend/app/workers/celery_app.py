from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "justbuildit",
    broker=settings.CELERY_BROKER_URL if hasattr(settings, "CELERY_BROKER_URL") else settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
