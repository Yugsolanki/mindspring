from app.schemas.website import WebsiteCreate, WebsiteResponse, WebsiteUpdate
from sqlalchemy import select
from app.models.website import Website
from app.core.logging import logger


class WebsiteRepository:
    def __init__(self, session):
        self.session = session

    async def get(self) -> WebsiteResponse:
        """
        Get the website
        Returns:
            WebsiteResponse: The website
        """
        try:
            result = await self.session.execute(select(Website).where(Website.id == 1))
            website = result.scalars().first()

            # Unlikely to happen due to lifespan config but why not
            if not website:
                return None

            return website
        except Exception as e:
            logger.exception(f"Error getting Website: {str(e)}")
            raise

    async def create(self, item_in: WebsiteCreate) -> WebsiteResponse:
        """
        Create a new website
        Args:
            item_in (WebsiteCreate): The website to create
        Returns:
            WebsiteResponse: The created website
        """
        try:
            new_website = Website(**item_in.model_dump())
            self.session.add(new_website)
            await self.session.commit()
            await self.session.refresh(new_website)
            return new_website
        except Exception as e:
            logger.exception(f"Error creating Website: {str(e)}")
            await self.session.rollback()
            raise

    async def update(self, id: int, item_in: WebsiteUpdate) -> WebsiteResponse | None:
        """
        Update a website
        Args:
            id (int): The id of the website to update
            item_in (WebsiteUpdate): The website to update
        Returns:
            WebsiteResponse | None: The updated website or None if not found
        """
        try:
            website = await self.get()
            if not website:
                return None

            for field, value in item_in.model_dump(exclude_unset=True).items():
                setattr(website, field, value)

            await self.session.commit()
            await self.session.refresh(website)
            return website
        except Exception as e:
            logger.exception(f"Error updating Website: {str(e)}")
            await self.session.rollback()
            raise

    async def delete(self, id: int) -> WebsiteResponse:
        """
        Delete a website
        Args:
            id (int): The id of the website to delete
        Returns:
            WebsiteResponse: The deleted website
        """
        try:
            website = await self.get()
            if not website:
                return None

            await self.session.delete(website)
            await self.session.commit()
            return website
        except Exception as e:
            logger.exception(f"Error deleting Website: {str(e)}")
            await self.session.rollback()
            raise
