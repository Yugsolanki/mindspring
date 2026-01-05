from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.scraped_content import ScrapedContent
from app.schemas.scraped_content import (
    ScrapedContentResponse,
    ScrapedContentUpdate,
)

router = APIRouter()


@router.get("/{content_id}", response_model=ScrapedContentResponse)
async def get_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific content chunk by ID.
    """
    result = await db.execute(
        select(ScrapedContent).where(ScrapedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return content


@router.patch("/{content_id}", response_model=ScrapedContentResponse)
async def update_content(
    content_id: int,
    content_in: ScrapedContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a specific content chunk.
    """
    result = await db.execute(
        select(ScrapedContent).where(ScrapedContent.id == content_id)
    )
    db_obj = result.scalar_one_or_none()

    if not db_obj:
        raise HTTPException(status_code=404, detail="Content not found")

    update_data = content_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific content chunk.
    """
    result = await db.execute(
        select(ScrapedContent).where(ScrapedContent.id == content_id)
    )
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(status_code=404, detail="Content not found")

    await db.delete(obj)
    await db.commit()
    return None
