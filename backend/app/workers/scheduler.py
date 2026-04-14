from celery.schedules import crontab
from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "send-due-date-reminders-daily": {
        "task": "app.workers.tasks.send_due_date_reminders",
        "schedule": crontab(hour=9, minute=0),  # every day at 9 AM UTC
    },
}

celery_app.conf.timezone = "UTC"
