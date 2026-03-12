from datetime import timedelta
from typing import List
from dataclasses import dataclass

from temporalio import activity
from temporalio.common import RetryPolicy

from app.schemas.content_scraper import ExtractedContent


@dataclass
class StoreContentInput:
    """Input for store content activity"""

    content_list: List[ExtractedContent]


@dataclass
class StoreContentResult:
    """Result of store content activity"""

    total_received: int
    content_stored: int
    content_updated: int
    content_skipped: int
    message: str


@activity.defn(name="store_content")
async def store_content_activity(input: StoreContentInput) -> StoreContentResult:
    """
    Activity that stores scraped content in the database.
    Equivalent to the Celery store_scraped_contents task.
    """
    extracted_content = input.content_list

    activity.logger.info(
        f"Starting store content activity: {len(extracted_content)} items"
    )
    activity.heartbeat("Checking existing content...")

    try:
        from app.core.database import get_session
        from app.repositories.scraped_content_repository import (
            ScrapedContentRepository,
        )
        from app.schemas.scraped_content import (
            ScrapedContentCreate,
            ScrapedContentUpdate,
        )
        from app.utils.text_diff import should_update

        # Extract resource IDs for existing content check
        resource_ids = [c.resource_id for c in extracted_content]

        async with get_session() as session:
            repo = ScrapedContentRepository(session=session)

            # Get existing records
            existing_content = await repo.get_all_by_resource_ids(resource_ids)
            existing_map = {c.resource_id: c for c in existing_content}

            # Prepare operations
            to_create: list[ScrapedContentCreate] = []
            to_update: list[tuple[int, ScrapedContentUpdate]] = []
            skipped = 0

            for idx, content in enumerate(extracted_content):
                # Periodic heartbeat for large batches
                if idx % 50 == 0:
                    activity.heartbeat(
                        f"Processing item {idx}/{len(extracted_content)}"
                    )

                payload = ScrapedContentCreate(
                    resource_id=content.resource_id,
                    url=content.url,
                    content_hash=content.content_hash,
                    content=content.markdown,
                    meta_data=content.metadata.model_dump(),
                )

                existing_record = existing_map.get(content.resource_id)

                if existing_record is None:
                    to_create.append(payload)
                elif should_update(
                    old_text=existing_record.content, new_text=content.markdown
                ):
                    update_payload = ScrapedContentUpdate(
                        content=content.markdown,
                        content_hash=content.content_hash,
                        meta_data=content.metadata.model_dump(),
                    )
                    to_update.append((content.resource_id, update_payload))
                else:
                    skipped += 1

            created_count = 0
            updated_count = 0

            if to_create:
                created_count = await repo.bulk_create_with_upsert(to_create)
            if to_update:
                updated_count = await repo.bulk_update(to_update)

            activity.logger.info(
                f"Stored {created_count} new content, {updated_count} updated, {skipped} skipped"
            )

            return StoreContentResult(
                total_received=len(extracted_content),
                content_stored=created_count,
                content_updated=updated_count,
                content_skipped=skipped,
                message=f"Content stored successfully: {created_count} content stored, {updated_count} updated, {skipped} skipped",
            )
    except Exception as e:
        activity.logger.error(f"Store content activity failed: {str(e)}")
        raise


STORE_CONTENT_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(minutes=30),
    "heartbeat_timeout": timedelta(seconds=30),
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=30),
        backoff_coefficient=2.0,
    ),
}
