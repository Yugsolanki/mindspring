from sqlalchemy import select
from app.models.website import Website
from app.core.database import SessionLocal
from app.schemas.website import WebsiteResponse
from fastapi import HTTPException
from typing import Optional


async def load_website() -> WebsiteResponse:
    async with SessionLocal() as db:
        result = await db.execute(select(Website).where(Website.id == 1))
        website: Optional[Website] = result.scalar_one_or_none()

        if not website:
            raise HTTPException(status_code=404, detail="Website not found")

        # Convert website to WebsiteResponse
        config: WebsiteResponse = WebsiteResponse.model_validate(
            website, from_attributes=True
        )

        return config
