import asyncio

from temporalio.worker import Worker

from app.core.temporal_client import get_temporal_client
from app.core.logging import logger
from app.temporal.activities.link_scraper_activity import (
    scrape_links_activity,
)
from app.temporal.activities.store_scraped_links_activity import (
    store_scraped_links_activity,
)
from app.temporal.workflows.link_scraper_workflow import LinkScraperWorkflow
from app.temporal.activities.content_scraper_activity import content_scraper_activity
from app.temporal.activities.store_content_activity import store_content_activity
from app.temporal.workflows.content_scraper_workflow import ContentScraperWorkflow
from app.core.config import settings


async def run_worker():
    """Run the Temporal worker"""
    logger.info("Starting Temporal worker")

    client = await get_temporal_client()

    logger.info(
        f"Temporal client connected, on task queue: {settings.TEMPORAL_TASK_QUEUE}"
    )

    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[LinkScraperWorkflow, ContentScraperWorkflow],
        activities=[
            scrape_links_activity,
            store_scraped_links_activity,
            content_scraper_activity,
            store_content_activity,
        ],
        # Workflow cache configuration
        max_cached_workflows=10,
        max_concurrent_workflow_tasks=10,
        max_concurrent_activities=5,
    )
    logger.info("Temporal worker started")

    await worker.run()


def main():
    """Main function to run the Temporal worker"""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Temporal worker stopped")
    except Exception as e:
        logger.error(f"Temporal worker failed: {e}")
        raise


if __name__ == "__main__":
    main()
