from app.schemas.scraped_content import (
    ScrapedContentCreate,
    ScrapedContentUpdate,
    ScrapedContentResponse,
)
from sqlalchemy import select, delete as delete_stmt, func
from app.models.scraped_content import ScrapedContent
from app.core.logging import logger
from app.core.exceptions import DatabaseException, NotFoundException
from sqlalchemy.dialects.postgresql import insert


class ScrapedContentRepository:
    def __init__(self, session):
        self.session = session

    async def get_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[ScrapedContentResponse]:
        try:
            result = await self.session.execute(
                select(ScrapedContent).offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error listing all scraped contents: {str(e)}")
            raise DatabaseException("Error listing all scraped contents")

    async def get_by_id(self, id: int) -> ScrapedContentResponse | None:
        try:
            result = await self.session.execute(
                select(ScrapedContent).where(ScrapedContent.id == id)
            )
            content = result.scalars().first()
            if not content:
                return NotFoundException("Scraped Content not found")
            return content
        except Exception as e:
            logger.exception(f"Error getting scraped content by id: {str(e)}")
            raise DatabaseException("Error getting scraped content by id")

    async def get_by_resource_id(
        self, resource_id: int
    ) -> ScrapedContentResponse | None:
        try:
            result = await self.session.execute(
                select(ScrapedContent).where(ScrapedContent.resource_id == resource_id)
            )
            content = result.scalars().first()
            if not content:
                return NotFoundException("Scraped Content not found")
            return content
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error getting scraped content by resource id: {str(e)}")
            raise DatabaseException("Error getting scraped content by resource id")

    async def get_all_by_resource_ids(
        self, resource_ids: list[int]
    ) -> list[ScrapedContentResponse]:
        try:
            result = await self.session.execute(
                select(ScrapedContent).where(
                    ScrapedContent.resource_id.in_(resource_ids)
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error getting scraped content by resource ids: {str(e)}")
            raise DatabaseException("Error getting scraped content by resource ids")

    async def create(
        self, item_in: ScrapedContentCreate
    ) -> ScrapedContentResponse | None:
        """
        Creates a new scraped content entry. Returns None if content_hash already exists.
        Returns the created object on success.
        """
        try:
            stmt = (
                insert(ScrapedContent)
                .values(item_in.model_dump())
                .on_conflict_do_nothing(index_elements=["content_hash"])
                .returning(ScrapedContent)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            created = result.scalar_one_or_none()
            return created
        except Exception as e:
            logger.exception(f"Error creating scraped content: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error creating scraped content")

    async def create_all(self, items_in: list[ScrapedContentCreate]):
        """
        Creates multiple scraped content entries. Skips duplicates based on content_hash.
        Returns list of successfully created objects.
        """
        try:
            stmt = (
                insert(ScrapedContent)
                .values([item.model_dump() for item in items_in])
                .on_conflict_do_nothing(index_elements=["content_hash"])
                .returning(ScrapedContent)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()
            created = result.scalars().all()
            return created
        except Exception as e:
            logger.exception(f"Error creating scraped contents: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error creating scraped contents")

    async def bulk_create(
        self, items: list[ScrapedContentCreate]
    ) -> list[ScrapedContent]:
        """
        Bulk creates scraped content entries. Skips duplicates based on content_hash.
        Returns list of successfully created objects.
        """
        try:
            values = [item.model_dump() for item in items]
            stmt = (
                insert(ScrapedContent)
                .values(values)
                .on_conflict_do_nothing(index_elements=["content_hash"])
                .returning(ScrapedContent)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Bulk create failed: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Bulk create failed")

    async def bulk_create_with_upsert(self, items: list[ScrapedContentCreate]) -> int:
        """
        Bulk creates or updates scraped content entries based on content_hash.
        Returns the number of rows affected.
        """
        try:
            values = [item.model_dump() for item in items]
            # Remove duplicates based on content_hash
            unique_values = {v["content_hash"]: v for v in values}

            stmt = insert(ScrapedContent).values(list(unique_values.values()))

            stmt = stmt.on_conflict_do_update(
                index_elements=["content_hash"],
                set_={
                    "content": stmt.excluded.content,
                    "meta_data": stmt.excluded.meta_data,
                    "url": stmt.excluded.url,
                    "updated_at": func.now(),
                },
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount if result.rowcount else 0
        except Exception as e:
            logger.exception(f"Bulk create with upsert failed: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Bulk create with upsert failed")

    async def bulk_update(self, updates: list[tuple[int, ScrapedContentUpdate]]) -> int:
        """
        Updates multiple scraped content entries by resource_id.
        Returns the count of updated records.
        """
        updated_count = 0
        try:
            for resource_id, item_in in updates:
                result = await self.session.execute(
                    select(ScrapedContent).where(
                        ScrapedContent.resource_id == resource_id
                    )
                )
                existing = result.scalars().first()
                if existing:
                    update_data = item_in.model_dump(exclude_unset=True)
                    for field, value in update_data.items():
                        setattr(existing, field, value)
                    updated_count += 1
            await self.session.commit()
            return updated_count
        except Exception as e:
            logger.exception(f"Bulk update failed: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Bulk update failed")

    async def update(
        self, id: int, item_in: ScrapedContentUpdate
    ) -> ScrapedContentResponse | None:
        try:
            content = await self.get_by_id(id=id)
            # get_by_id now raises NotFoundException if not found, so no need to check

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(content, field, value)

            await self.session.commit()
            await self.session.refresh(content)
            return content
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error updating scraped content: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error updating scraped content")

    async def update_by_resource_id(
        self, resource_id: int, item_in: ScrapedContentUpdate
    ) -> ScrapedContentResponse | None:
        try:
            content = await self.get_by_resource_id(resource_id=resource_id)
            # get_by_resource_id now raises NotFoundException if not found

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(content, field, value)

            await self.session.commit()
            await self.session.refresh(content)
            return content
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error updating scraped content by resource id: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error updating scraped content by resource id")

    async def delete(self, id: int) -> ScrapedContentResponse:
        try:
            content = await self.get_by_id(id=id)

            await self.session.delete(content)
            await self.session.commit()
            return content
        except NotFoundException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting scraped content: {str(e)}")
            await self.session.rollback()
            raise DatabaseException("Error deleting scraped content")

    async def delete_all(self) -> int:
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
            raise DatabaseException("Error deleting all scraped contents")
