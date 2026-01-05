from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.scraped_resource import ScrapedResource
from app.models.scraped_content import ScrapedContent
from app.schemas.scraped_resource import (
    ScrapedResourceResponse,
    ScrapedResourceCreate,
    ScrapedResourceUpdate,
    ScrapedResourceWithContents,
)
from app.schemas.scraped_content import (
    ScrapedContentResponse,
    ScrapedContentCreate,
)

router = APIRouter()


# =======================================================================
# Scraped Resource
# =======================================================================


@router.post(
    "/", response_model=ScrapedResourceResponse, status_code=status.HTTP_201_CREATED
)
async def create_resource(
    resource_in: ScrapedResourceCreate, db: AsyncSession = Depends(get_db)
):
    """
    Register a new URL to be scraped. Does not contain content yet.
    """
    db_obj = ScrapedResource(**resource_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/", response_model=list[ScrapedResourceResponse])
async def list_resources(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """
    List all scraped resources (pagination supported).
    """

    query = select(ScrapedResource).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{resource_id}", response_model=ScrapedResourceWithContents)
async def get_resource(resource_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific resource including its scraped text content chunks.
    """
    # We need to eager load the contents or select them separately.
    # For simplicity in this example, we select the resource and rely on
    # the relationship attribute, but in production use `selectinload`.
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(ScrapedResource)
        .options(selectinload(ScrapedResource.contents))
        .where(ScrapedResource.id == resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource


@router.patch("/{resource_id}", response_model=ScrapedResourceResponse)
async def update_resource(
    resource_id: int,
    resource_in: ScrapedResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update resource details (e.g., URL or status).
    """
    result = await db.execute(
        select(ScrapedResource).where(ScrapedResource.id == resource_id)
    )
    db_obj = result.scalar_one_or_none()

    if not db_obj:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Update fields dynamically based on input
    update_data = resource_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a resource.
    """
    # Simple approach: select then delete (allows for cascade checks)
    result = await db.execute(
        select(ScrapedResource).where(ScrapedResource.id == resource_id)
    )
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(obj)
    await db.commit()
    return None


# =======================================================================
# Scraped Content
# =======================================================================


@router.post("/{resource_id}/content", response_model=ScrapedContentResponse)
async def add_content_to_resource(
    resource_id: int,
    content_in: ScrapedContentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a text block (and embeddings) to a specific resource.
    """
    # Verify resource exists
    result = await db.execute(
        select(ScrapedResource).where(ScrapedResource.id == resource_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Resource not found")

    # Create content
    # Ensure we link the resource_id in the content object
    db_obj = ScrapedContent(**content_in.model_dump())
    db_obj.resource_id = resource_id
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
