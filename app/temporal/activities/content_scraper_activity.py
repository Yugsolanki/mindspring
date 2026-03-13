from dataclasses import dataclass
from datetime import timedelta
from typing import List

from temporalio import activity
from temporalio.common import RetryPolicy

from app.schemas.content_scraper import ExtractedContent


@dataclass
class ContentScraperResult:
    """Result of content scraper activity"""

    content_list: List[ExtractedContent]
    success_count: int
    failed_count: int


@activity.defn(name="scrape_content")
async def content_scraper_activity() -> ContentScraperResult:
    """
    Activity that scrapes content from the target source.
    """
    activity.logger.info("Starting content scraper activity")

    # Progress callback to update Temporal server with scraping progress
    async def progress_callback(progress: str):
        activity.heartbeat(progress)

    # Heartbeat to prevent timeout during long scraping operations
    activity.heartbeat("Starting content scraper...")

    try:
        from app.services.content_scraper import run_content_scraper, ScrapeConfig

        config = ScrapeConfig(batch_size=20, max_retries=3, timeout_seconds=45)
        content_list, success_count, failed_count = await run_content_scraper(
            progress_callback=progress_callback,
            config=config,
        )

        activity.heartbeat(f"Scraped {len(content_list)} URLs")
        activity.logger.info(f"Scraper found {len(content_list)} URLs")

        return ContentScraperResult(
            content_list=content_list,
            success_count=success_count,
            failed_count=failed_count,
        )
    except Exception as e:
        activity.logger.info(f"Scraper failed: {e}")
        raise


CONTENT_SCRAPER_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(hours=6),
    "heartbeat_timeout": timedelta(minutes=2),
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(minutes=5),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=5),
    ),
}
