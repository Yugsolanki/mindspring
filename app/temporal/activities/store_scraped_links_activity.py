from datetime import timedelta
from typing import List
from dataclasses import dataclass

from temporalio import activity
from temporalio.common import RetryPolicy


@dataclass
class StoreLinksInput:
    """Input for store scraped links activity"""

    links: List[str]


@dataclass
class StoreLinksResult:
    """Result of store scraped links activity"""

    total_received: int
    new_links_stored: int
    duplicates_skipped: int
    message: str


@activity.defn(name="store_scraped_links")
async def store_scraped_links_activity(input: StoreLinksInput) -> StoreLinksResult:
    """
    Activity that stores scraped links in the database.
    Equivalent to the Celery store_scraped_links task.
    """
    all_links = input.links

    activity.logger.info(
        f"Starting store scraped links activity: {len(all_links)} links"
    )
    activity.heartbeat("Checking existing URL's...")

    try:
        from app.core.database import get_session
        from app.repositories.scraped_resources_repository import (
            ScrapedResourcesRepository,
        )
        from app.schemas.scraped_resource import ScrapedResourceCreate
        from app.utils.mimetypes import infer_file_type_from_url

        async with get_session() as session:
            repo = ScrapedResourcesRepository(session=session)
            existing_urls = set(await repo.get_urls())

            activity.heartbeat(f"Found {len(existing_urls)} existing URL's")

            new_scraped_resources = []

            for idx, link in enumerate(all_links):
                # Periodic heartbeat for large batches
                if idx % 100 == 0:
                    activity.heartbeat(f"Processing link {idx}/{len(all_links)}")

                if link not in existing_urls:
                    new_scraped_resources.append(
                        ScrapedResourceCreate(
                            url=link,
                            content_type=infer_file_type_from_url(link),
                            scrape_status="pending",
                        )
                    )

            if new_scraped_resources:
                activity.heartbeat(f"Storing {len(new_scraped_resources)} new links...")
                await repo.create_all(new_scraped_resources)

            duplicates = len(all_links) - len(new_scraped_resources)

            activity.logger.info(
                f"Stored {len(new_scraped_resources)} new scraped links, skipped {duplicates} duplicates"
            )

            return StoreLinksResult(
                total_received=len(all_links),
                new_links_stored=len(new_scraped_resources),
                duplicates_skipped=duplicates,
                message=f"Scraped links stored successfully: {len(new_scraped_resources)} links stored",
            )
    except Exception as e:
        activity.logger.error(f"Store scraped links activity failed: {str(e)}")
        raise


STORE_LINKS_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(minutes=5),
    "heartbeat_timeout": timedelta(seconds=30),
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=30),
        backoff_coefficient=2.0,
    ),
}
