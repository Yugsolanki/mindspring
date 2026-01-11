from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.scraped_content import (
    ScrapedContentResponse,
    ScrapedContentUpdate,
)
from app.repositories.scraped_content_repository import ScrapedContentRepository
from app.core.response import SuccessResponseModel

router = APIRouter()


@router.get(
    "/{content_id}", response_model=SuccessResponseModel[ScrapedContentResponse]
)
async def get_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific content chunk by ID.
    """
    content = await ScrapedContentRepository(db).get_by_id(id=content_id)
    return SuccessResponseModel(data=content)


@router.patch(
    "/{content_id}", response_model=SuccessResponseModel[ScrapedContentResponse]
)
async def update_content(
    content_id: int,
    content_in: ScrapedContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a specific content chunk.
    """
    content = await ScrapedContentRepository(db).update(
        id=content_id, item_in=content_in
    )
    return SuccessResponseModel(data=content)


@router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific content chunk.
    """
    await ScrapedContentRepository(db).delete(id=content_id)
