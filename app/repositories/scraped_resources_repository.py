from app.schemas.scraped_resource import (
    ScrapedResourceCreate,
    ScrapedResourceUpdate,
    ScrapedResourceResponse,
    ScrapedResourceWithContents,
)
from sqlalchemy import select, delete, func
from app.models.scraped_resource import ScrapedResource
from app.core.logging import logger

# from sqlalchemy.ext.asyncio import AsyncSession


class ScrapedResourcesRepository:
    def __init__(self, session):
        self.session = session

    async def list_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[ScrapedResourceResponse]:
        try:
            result = await self.session.execute(
                select(ScrapedResource).offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise

    async def list_urls(self) -> list[str]:
        try:
            result = await self.session.execute(select(ScrapedResource.url))
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise

    async def get_by_id(self, id: int) -> ScrapedResourceWithContents | None:
        try:
            result = await self.session.execute(
                select(ScrapedResource).where(ScrapedResource.id == id)
            )
            resource = result.scalars().first()
            if not resource:
                return None
            return resource
        except Exception as e:
            logger.exception(f"Error getting scraped resource by id: {str(e)}")
            raise

    async def create(self, item_in: ScrapedResourceCreate) -> ScrapedResourceResponse:
        try:
            new_scraped_resource = ScrapedResource(**item_in.model_dump())
            self.session.add(new_scraped_resource)

            await self.session.commit()
            await self.session.refresh(new_scraped_resource)
            return new_scraped_resource
        except Exception as e:
            logger.exception(f"Error creating scraped resource: {str(e)}")
            await self.session.rollback()
            raise

    async def create_all(
        self, items_in: list[ScrapedResourceCreate]
    ) -> list[ScrapedResourceResponse]:
        try:
            new_scraped_resources = [
                ScrapedResource(**item_in.model_dump()) for item_in in items_in
            ]

            self.session.add_all(new_scraped_resources)
            await self.session.commit()
            return new_scraped_resources
        except Exception as e:
            logger.exception(f"Error creating scraped resources: {str(e)}")
            await self.session.rollback()
            raise

    async def update(
        self, id: int, item_in: ScrapedResourceUpdate
    ) -> ScrapedResourceResponse | None:
        try:
            resource = await self.get_by_id(id=id)
            if not resource:
                return None

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(resource, field, value)

            await self.session.commit()
            await self.session.refresh(resource)
            return resource
        except Exception as e:
            logger.exception(f"Error updating scraped resource: {str(e)}")
            await self.session.rollback()
            raise

    async def delete(self, id: int) -> ScrapedResourceResponse:
        try:
            resource = await self.get_by_id(id=id)
            if not resource:
                return None

            await self.session.delete(resource)
            await self.session.commit()
            return resource
        except Exception as e:
            logger.exception(f"Error deleting scraped resource: {str(e)}")
            await self.session.rollback()
            raise

    async def delete_all(self) -> int:
        try:
            count_stmt = select(func.count(ScrapedResource.id))
            count_result = await self.session.execute(count_stmt)
            count = count_result.scalar()

            await self.session.execute(delete(ScrapedResource))
            await self.session.commit()
            return count
        except Exception as e:
            logger.exception(f"Error deleting all scraped resources: {str(e)}")
            await self.session.rollback()
            raise
