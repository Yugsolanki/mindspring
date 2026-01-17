from celery import shared_task
from app.core.logging import logger
from app.core.singleton_task import singleton_task
from app.utils.async_utils import run_async


def _run_scraper():
    from app.services.content_scraper import run_content_scraper, ScrapeConfig

    config = ScrapeConfig(batch_size=20, max_retries=3, timeout_seconds=45)
    return run_async(run_content_scraper(config))


@shared_task(
    name="content_scraper",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=60,
)
@singleton_task("content_scraper", heartbeat_interval=30, stale_after=120)
def content_scraper(self):
    logger.info("Starting content scraper task")
    return _run_scraper()
