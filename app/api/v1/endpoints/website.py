from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.website import Website
from app.schemas.website import WebsiteResponse, WebsiteUpdate, WebsiteCreate

router = APIRouter()


@router.get("/", response_model=WebsiteResponse)
async def get_website_config(db: AsyncSession = Depends(get_db)):
    """
    Get the current global website scraping configuration.
    """

    query = select(Website).where(Website.id == 1)
    result = await db.execute(query)
    website = result.scalars().first()

    if not website:
        # This theoretically shouldn't happen because of lifespan script,
        # but it's good practice to handle it.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website configuration not initialized.",
        )

    return website


@router.patch("/", response_model=WebsiteResponse)
async def update_website_config(
    item_in: WebsiteUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update specific fields of the website configuration.
    Only fields sent in the JSON body will be updated.
    """
    # 1. Fetch existing
    query = select(Website).where(Website.id == 1)
    result = await db.execute(query)
    website = result.scalars().first()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website configuration not found.",
        )

    # 2. Update fields
    # exclude_unset=True is CRITICAL here.
    # It ensures we only update fields the user actually sent.
    update_data = item_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(website, field, value)

    # 3. Save
    await db.commit()
    await db.refresh(website)  # Reloads data from DB (updates updated_at timestamp)

    return website


@router.put("/", response_model=WebsiteResponse)
async def replace_website_config(
    item_in: WebsiteCreate, db: AsyncSession = Depends(get_db)  # Requires all fields
):
    """
    Full update. Replaces all setting fields with the provided values.
    """
    query = select(Website).where(Website.id == 1)
    result = await db.execute(query)
    website = result.scalars().first()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website configuration not found.",
        )

    # Update all fields allowed in WebsiteCreate
    update_data = item_in.model_dump()
    for field, value in update_data.items():
        setattr(website, field, value)

    await db.commit()
    await db.refresh(website)

    return website
