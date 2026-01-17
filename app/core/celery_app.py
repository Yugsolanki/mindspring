from celery import Celery, current_app
from app.core.config import settings

# fmt: off
from app.workers import (link_scraper, content_scraper, store_scraped_contents, store_scraped_links)  # noqa
# fmt: on


def make_celery():
    celery_app = current_app if current_app else Celery("mindspring")
    celery_app.conf.update(
        broker_url=settings.REDIS_URL,
        result_backend=settings.REDIS_URL,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,
        task_track_started=True,
        result_expires=3600,
    )
    celery_app.autodiscover_tasks(["app.workers"], related_name="workers")
    return celery_app


celery_app = make_celery()
