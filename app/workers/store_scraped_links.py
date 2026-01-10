from celery import shared_task
from app.repositories.scraped_resources_repository import ScrapedResourcesRepository
from app.schemas.scraped_resource import ScrapedResourceCreate
from app.utils.mimetypes import infer_file_type_from_url
from app.core.response import SuccessResponseModel
from app.utils.async_utils import run_async
from app.core.logging import logger
from app.core.database import get_session


@shared_task(
    name="store_scraped_links",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=30,
)
def store_scraped_links(self, all_links: list[str]):
    return run_async(_store_scraped_links(all_links))


async def _store_scraped_links(all_links: list[str]):
    """
    Store scraped links in database
    """
    logger.info(f"Starting store scraped links task: {len(all_links)} links")

    async with get_session() as session:
        repo = ScrapedResourcesRepository(session=session)
        existing_urls = set(await repo.list_urls())

        new_scraped_resources = []

        for link in all_links:
            if link not in existing_urls:
                new_scraped_resources.append(
                    ScrapedResourceCreate(
                        url=link,
                        content_type=infer_file_type_from_url(link),
                        scrape_status="pending",
                    )
                )

        if new_scraped_resources:
            await repo.create_all(new_scraped_resources)

    logger.info(f"Stored {len(new_scraped_resources)} new scraped links")

    return SuccessResponseModel(
        message=f"Scraped links stored successfully: {len(new_scraped_resources)} links stored",
    ).model_dump_json()
