from app.schemas.scraped_resource import (
    ScrapedResourceCreate,
    ScrapedResourceUpdate,
    ScrapedResourceResponse,
)
from app.schemas.scraped_content import ScrapedContentCreate, ScrapedContentResponse
from sqlalchemy import select, delete as delete_stmt, func
from app.models.scraped_resource import ScrapedResource
from app.models.scraped_content import ScrapedContent
from app.core.logging import logger
from app.core.exceptions import DatabaseException, NotFoundException
from sqlalchemy.dialects.postgresql import insert


class ScrapedResourcesRepository:
    def __init__(self, session):
        self.session = session

    async def get_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[ScrapedResourceResponse]:
        try:
            result = await self.session.execute(
                select(ScrapedResource).offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise DatabaseException("Error listing all scraped resources")

    async def get_urls(self) -> list[str]:
        try:
            result = await self.session.execute(select(ScrapedResource.url))
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise DatabaseException("Error listing all scraped resources")

    async def get_urls_and_ids(self) -> list[tuple[str, int]]:
        try:
            result = await self.session.execute(
                select(ScrapedResource.url, ScrapedResource.id)
            )
            return result.all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise DatabaseException("Error listing all scraped resources")

    async def get_by_id(self, id: int) -> ScrapedContentResponse | None:
        try:
            result = await self.session.execute(
                select(ScrapedResource).where(ScrapedResource.id == id)
            )
            resource = result.scalars().first()
            if not resource:
                return NotFoundException("Scraped Resource not found")
            return resource
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error getting scraped resource by id: {str(e)}")
            raise DatabaseException("Error getting scraped resource by id")

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
            raise DatabaseException("Error creating scraped resource")

    async def create_all(
        self, items_in: list[ScrapedResourceCreate]
    ) -> list[ScrapedResourceResponse]:
        try:
            stmt = (
                insert(ScrapedResource)
                .values([item.model_dump() for item in items_in])
                .returning(ScrapedResource)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error creating scraped resources: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error creating scraped resources")

    async def update(
        self, id: int, item_in: ScrapedResourceUpdate
    ) -> ScrapedResourceResponse | None:
        try:
            resource = await self.get_by_id(id=id)

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(resource, field, value)

            await self.session.commit()
            await self.session.refresh(resource)
            return resource
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error updating scraped resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error updating scraped resource")

    async def delete(self, id: int) -> ScrapedResourceResponse:
        try:
            resource = await self.get_by_id(id=id)

            await self.session.delete(resource)
            await self.session.commit()
            return resource
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting scraped resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error deleting scraped resource")

    async def delete_all(self) -> int:
        try:
            count_stmt = select(func.count(ScrapedResource.id))
            count_result = await self.session.execute(count_stmt)
            count = count_result.scalar()

            await self.session.execute(delete_stmt(ScrapedResource))
            await self.session.commit()
            return count
        except Exception as e:
            logger.exception(f"Error deleting all scraped resources: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error deleting all scraped resources")

    async def add_content(
        self, resource_id: int, content_in: ScrapedContentCreate
    ) -> ScrapedContentResponse:
        try:
            content = ScrapedContent(**content_in.model_dump())
            content.resource_id = resource_id
            self.session.add(content)
            await self.session.commit()
            await self.session.refresh(content)
            return content
        except Exception as e:
            logger.exception(f"Error adding content to resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error adding content to resource")

    async def add_content_all(
        self, resource_id: int, content_in: list[ScrapedContentCreate]
    ) -> list[ScrapedContentResponse]:
        try:
            contents = [
                ScrapedContent(**content_in.model_dump()) for content_in in content_in
            ]
            for content in contents:
                content.resource_id = resource_id

            stmt = (
                insert(ScrapedContent)
                .values([content.model_dump() for content in contents])
                .returning(ScrapedContent)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error adding content to resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error adding content to resource")
