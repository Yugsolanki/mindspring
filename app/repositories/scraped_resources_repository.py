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


class ScrapedResourcesRepository:
    def __init__(self, session):
        self.session = session

    async def get_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[ScrapedResourceResponse]:
        """
        List all scraped resources
        Args:
            offset (int): The offset to start from
            limit (int): The limit of results to return
        Returns:
            list[ScrapedResourceResponse]: The list of scraped resources
        """
        try:
            result = await self.session.execute(
                select(ScrapedResource).offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise DatabaseException("Error listing all scraped resources")

    async def get_urls(self) -> list[str]:
        """
        List all scraped resource urls
        Returns:
            list[str]: The list of scraped resource urls
        """
        try:
            result = await self.session.execute(select(ScrapedResource.url))
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped resources: {str(e)}")
            raise DatabaseException("Error listing all scraped resources")

    async def get_by_id(self, id: int) -> ScrapedContentResponse | None:
        """
        Get a scraped resource by id
        Args:
            id (int): The id of the scraped resource to get
        Returns:
            ScrapedResourceWithContents | None: The scraped resource or None if not found
        """
        try:
            result = await self.session.execute(
                select(ScrapedResource).where(ScrapedResource.id == id)
            )
            resource = result.scalars().first()
            if not resource:
                return NotFoundException("Scraped Resource not found")
            return resource
        except Exception as e:
            logger.exception(f"Error getting scraped resource by id: {str(e)}")
            raise DatabaseException("Error getting scraped resource by id")

    async def create(self, item_in: ScrapedResourceCreate) -> ScrapedResourceResponse:
        """
        Create a new scraped resource
        Args:
            item_in (ScrapedResourceCreate): The scraped resource to create
        Returns:
            ScrapedResourceResponse: The created scraped resource
        """
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
        """
        Create multiple new scraped resources
        Args:
            items_in (list[ScrapedResourceCreate]): The scraped resources to create
        Returns:
            list[ScrapedResourceResponse]: The created scraped resources
        """
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
            raise DatabaseException("Error creating scraped resources")

    async def update(
        self, id: int, item_in: ScrapedResourceUpdate
    ) -> ScrapedResourceResponse | None:
        """
        Update a scraped resource
        Args:
            id (int): The id of the scraped resource to update
            item_in (ScrapedResourceUpdate): The scraped resource to update
        Returns:
            ScrapedResourceResponse | None: The updated scraped resource or None if not found
        """
        try:
            resource = await self.get_by_id(id=id)
            if not resource:
                return NotFoundException("Scraped Resource not found")

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(resource, field, value)

            await self.session.commit()
            await self.session.refresh(resource)
            return resource
        except Exception as e:
            logger.exception(f"Error updating scraped resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error updating scraped resource")

    async def delete(self, id: int) -> ScrapedResourceResponse:
        """
        Delete a scraped resource
        Args:
            id (int): The id of the scraped resource to delete
        Returns:
            ScrapedResourceResponse: The deleted scraped resource
        """
        try:
            resource = await self.get_by_id(id=id)
            if not resource:
                return NotFoundException("Scraped Resource not found")

            await self.session.delete(resource)
            await self.session.commit()
            return resource
        except Exception as e:
            logger.exception(f"Error deleting scraped resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error deleting scraped resource")

    async def delete_all(self) -> int:
        """
        Delete all scraped resources
        Returns:
            int: The number of deleted scraped resources
        """
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
        """
        Add a text block (and embeddings) to a specific resource.
        Args:
            resource_id (int): The id of the resource to add content to
            content_in (ScrapedContentCreate): The content to add
        Returns:
            ScrapedContentResponse: The added content
        """
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
        """
        Add multiple text blocks (and embeddings) to a specific resource.
        Args:
            resource_id (int): The id of the resource to add content to
            content_in (list[ScrapedContentCreate]): The content to add
        Returns:
            list[ScrapedContentResponse]: The added content
        """
        try:
            contents = [
                ScrapedContent(**content_in.model_dump()) for content_in in content_in
            ]
            for content in contents:
                content.resource_id = resource_id
            self.session.add_all(contents)
            await self.session.commit()
            return contents
        except Exception as e:
            logger.exception(f"Error adding content to resource: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error adding content to resource")
