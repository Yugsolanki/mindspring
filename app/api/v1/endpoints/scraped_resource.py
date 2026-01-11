from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.scraped_resource import (
    ScrapedResourceResponse,
    ScrapedResourceCreate,
    ScrapedResourceUpdate,
)
from app.schemas.scraped_content import (
    ScrapedContentResponse,
    ScrapedContentCreate,
)
from app.repositories.scraped_resources_repository import ScrapedResourcesRepository
from app.core.response import SuccessResponseModel

router = APIRouter()


# =======================================================================
# Scraped Resource
# =======================================================================


@router.post(
    "/",
    response_model=SuccessResponseModel[ScrapedResourceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
    resource_in: ScrapedResourceCreate, db: AsyncSession = Depends(get_db)
):
    """
    Register a new URL to be scraped. Does not contain content yet.
    """
    resource = await ScrapedResourcesRepository(db).create(item_in=resource_in)
    return SuccessResponseModel(data=resource)


@router.get("/", response_model=SuccessResponseModel[list[ScrapedResourceResponse]])
async def list_resources(
    offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """
    List all scraped resources (pagination supported).
    """
    resources = await ScrapedResourcesRepository(db).get_all(offset=offset, limit=limit)
    return SuccessResponseModel(data=resources)


@router.get(
    "/{resource_id}", response_model=SuccessResponseModel[ScrapedResourceResponse]
)
async def get_resource(resource_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific resource including its scraped text content chunks.
    """
    resource = await ScrapedResourcesRepository(db).get_by_id(id=resource_id)
    return SuccessResponseModel(data=resource)


@router.patch(
    "/{resource_id}", response_model=SuccessResponseModel[ScrapedResourceResponse]
)
async def update_resource(
    resource_id: int,
    resource_in: ScrapedResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update resource details (e.g., URL or status).
    """
    resource = await ScrapedResourcesRepository(db).update(
        id=resource_id, item_in=resource_in
    )
    return SuccessResponseModel(data=resource)


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_resource(resource_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a resource.
    """
    await ScrapedResourcesRepository(db).delete(id=resource_id)


# =======================================================================
# Scraped Content
# =======================================================================


@router.post(
    "/{resource_id}/content",
    response_model=SuccessResponseModel[ScrapedContentResponse],
)
async def add_content_to_resource(
    resource_id: int,
    content_in: ScrapedContentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a text block (and embeddings) to a specific resource.
    """
    content = await ScrapedResourcesRepository(db).add_content(
        resource_id=resource_id, content_in=content_in
    )
    return SuccessResponseModel(data=content)
