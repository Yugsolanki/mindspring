from celery import shared_task
from app.services.link_scraper import run_scraper
from app.core.logging import logger
from app.utils.async_utils import run_async


@shared_task(
    name="link_scraper",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=30,
)
def link_scraper(self):
    logger.info("Starting link scraper task")
    return run_async(run_scraper())
