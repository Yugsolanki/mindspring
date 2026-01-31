from datetime import timedelta
from dataclasses import dataclass
from typing import List

from temporalio import activity
from temporalio.common import RetryPolicy


@dataclass
class LinkScraperResult:
    """Result of link scraper activity"""

    links: List[str]
    count: int


@activity.defn(name="scrape_links")
async def scrape_links_activity() -> LinkScraperResult:
    """
    Activity that scrapes links from the target source.
    """
    activity.logger.info("Starting link scraper activity")

    # Progress callback to update Temporal server with scraping progress
    async def progress_callback(progress: str):
        activity.heartbeat(progress)

    # Heartbeat to prevent timeout during long scraping operations
    activity.heartbeat("Starting link scraper...")

    try:
        from app.services.link_scraper import run_scraper

        links = await run_scraper(progress_callback=progress_callback)

        activity.heartbeat(f"Scraped {len(links)}")
        activity.logger.info(f"Scraper found {len(links)} links")

        return LinkScraperResult(links=links, count=len(links))
    except Exception as e:
        activity.logger.info(f"Scraper failed: {e}")
        # Re-raising to trigger Temporal retry
        raise


SCRAPE_LINKS_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(hours=3),
    "heartbeat_timeout": timedelta(seconds=30),
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(minutes=5),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=5),
    ),
}
