# Celery Configuration for Background Tasks
"""
Celery app configuration for async video processing
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    'viralclip',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.services.pipeline']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
)

# Optional: Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'app.services.cleanup.cleanup_old_jobs',
        'schedule': 3600.0,  # Run every hour
    },
}
