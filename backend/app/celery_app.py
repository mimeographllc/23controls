"""
Celery Application Configuration
Async task processing for SynthetIQ Signals CDP
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "synthetiq_cdp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email",
        "app.tasks.models",
        "app.tasks.reports",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    # Example: Clean up expired sessions every hour
    "cleanup-expired-sessions": {
        "task": "app.tasks.email.cleanup_expired_sessions",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Example: Generate daily reports at midnight
    "generate-daily-reports": {
        "task": "app.tasks.reports.generate_daily_report",
        "schedule": crontab(hour=0, minute=0),  # Midnight UTC
    },
}

# Task routes (optional - for task-specific queues)
celery_app.conf.task_routes = {
    "app.tasks.email.*": {"queue": "emails"},
    "app.tasks.reports.*": {"queue": "reports"},
    "app.tasks.models.*": {"queue": "models"},
}


# Utility function for sending tasks
def send_task(task_name: str, *args, **kwargs):
    """Send a task to Celery"""
    return celery_app.send_task(task_name, args=args, kwargs=kwargs)
