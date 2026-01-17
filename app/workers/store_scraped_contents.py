from celery import shared_task
from app.repositories.scraped_content_repository import ScrapedContentRepository
from app.core.response import SuccessResponseModel
from app.utils.async_utils import run_async
from app.core.logging import logger
from app.core.database import get_session
from app.schemas.content_scraper import ExtractedContent
from app.schemas.scraped_content import ScrapedContentCreate, ScrapedContentUpdate
from app.utils.text_diff import should_update
from sqlalchemy.exc import OperationalError


@shared_task(
    name="store_scraped_contents",
    bind=True,
    autoretry_for=(OperationalError,),
    max_retries=3,
    retry_backoff=30,
)
def store_scraped_contents(self, extracted_content: list[dict]):
    logger.info(f"Store task received {len(extracted_content)} items")
    content_objects = [ExtractedContent(**item) for item in extracted_content]
    return run_async(_store_scraped_contents(content_objects))


async def _store_scraped_contents(
    extracted_content: list[ExtractedContent],
) -> str:
    logger.info(f"Processing {len(extracted_content)} scraped contents")

    valid_content = [c for c in extracted_content if c.success and c.resource_id > 0]
    if not valid_content:
        logger.info("No valid content to store")
        return SuccessResponseModel(
            message="No valid content to store"
        ).model_dump_json()

    resource_ids = [c.resource_id for c in valid_content]

    try:
        async with get_session() as session:
            repo = ScrapedContentRepository(session=session)
            existing = await repo.get_all_by_resource_ids(resource_ids)
            # Map existing records by resource ID
            existing_map = {c.resource_id: c for c in existing}

            to_create: list[ScrapedContentCreate] = []
            to_update: list[tuple[int, ScrapedContentUpdate]] = []
            skipped = 0

            for content in valid_content:
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

    except Exception as e:
        logger.exception(f"Failed to store scraped contents: {str(e)}")
        return SuccessResponseModel(
            message=f"Failed to store contents: {str(e)}"
        ).model_dump_json()

    logger.info(
        f"Stored: {created_count} created, {updated_count} updated, {skipped} skipped"
    )

    return SuccessResponseModel(
        message=f"Processed: {created_count} created, {updated_count} updated, {skipped} skipped"
    ).model_dump_json()
