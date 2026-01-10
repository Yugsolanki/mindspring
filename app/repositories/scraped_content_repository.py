from app.schemas.scraped_content import (
    ScrapedContentCreate,
    ScrapedContentUpdate,
    ScrapedContentResponse,
)
from sqlalchemy import select, delete as delete_stmt, func
from app.models.scraped_content import ScrapedContent
from app.core.logging import logger


class ScrapedContentRepository:
    def __init__(self, session):
        self.session = session

    async def list_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[ScrapedContentResponse]:
        """
        List all scraped contents
        Args:
            offset (int): The offset to start from
            limit (int): The limit of results to return
        Returns:
            list[ScrapedContentResponse]: The list of scraped contents
        """
        try:
            result = await self.session.execute(
                select(ScrapedContent).offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped contents: {str(e)}")
            raise

    async def get_by_id(self, id: int) -> ScrapedContentResponse | None:
        """
        Get a scraped content by id
        Args:
            id (int): The id of the scraped content to get
        Returns:
            ScrapedContentResponse | None: The scraped content or None if not found
        """
        try:
            result = await self.session.execute(
                select(ScrapedContent).where(ScrapedContent.id == id)
            )
            content = result.scalars().first()
            if not content:
                return None
            return content
        except Exception as e:
            logger.exception(f"Error getting scraped content by id: {str(e)}")
            raise

    async def create(self, item_in: ScrapedContentCreate) -> ScrapedContentResponse:
        """
        Create a new scraped content
        Args:
            item_in (ScrapedContentCreate): The scraped content to create
        Returns:
            ScrapedContentResponse: The created scraped content
        """
        try:
            new_scraped_content = ScrapedContent(**item_in.model_dump())
            self.session.add(new_scraped_content)

            await self.session.commit()
            await self.session.refresh(new_scraped_content)
            return new_scraped_content
        except Exception as e:
            logger.exception(f"Error creating scraped content: {str(e)}")
            await self.session.rollback()
            raise

    async def create_all(
        self, items_in: list[ScrapedContentCreate]
    ) -> list[ScrapedContentResponse]:
        """
        Create multiple new scraped contents
        Args:
            items_in (list[ScrapedContentCreate]): The scraped contents to create
        Returns:
            list[ScrapedContentResponse]: The created scraped contents
        """
        try:
            new_scraped_contents = [
                ScrapedContent(**item_in.model_dump()) for item_in in items_in
            ]

            self.session.add_all(new_scraped_contents)
            await self.session.commit()
            return new_scraped_contents
        except Exception as e:
            logger.exception(f"Error creating scraped contents: {str(e)}")
            await self.session.rollback()
            raise

    async def update(
        self, id: int, item_in: ScrapedContentUpdate
    ) -> ScrapedContentResponse | None:
        """
        Update a scraped content
        Args:
            id (int): The id of the scraped content to update
            item_in (ScrapedContentUpdate): The scraped content to update
        Returns:
            ScrapedContentResponse | None: The updated scraped content or None if not found
        """
        try:
            content = await self.get_by_id(id=id)
            if not content:
                return None

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(content, field, value)

            await self.session.commit()
            await self.session.refresh(content)
            return content
        except Exception as e:
            logger.exception(f"Error updating scraped content: {str(e)}")
            await self.session.rollback()
            raise

    async def delete(self, id: int) -> ScrapedContentResponse:
        """
        Delete a scraped content
        Args:
            id (int): The id of the scraped content to delete
        Returns:
            ScrapedContentResponse: The deleted scraped content
        """
        try:
            content = await self.get_by_id(id=id)
            if not content:
                return None

            await self.session.delete(content)
            await self.session.commit()
            return content
        except Exception as e:
            logger.exception(f"Error deleting scraped content: {str(e)}")
            await self.session.rollback()
            raise

    async def delete_all(self) -> int:
        """
        Delete all scraped contents
        Returns:
            int: The number of deleted scraped contents
        """
        try:
            count_stmt = select(func.count()).select_from(ScrapedContent)
            count_result = await self.session.execute(count_stmt)
            count = count_result.scalar()

            await self.session.execute(delete_stmt(ScrapedContent))
            await self.session.commit()
            return count
        except Exception as e:
            logger.exception(f"Error deleting all scraped contents: {str(e)}")
            await self.session.rollback()
            raise
