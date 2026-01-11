from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.website import WebsiteResponse, WebsiteUpdate
from app.repositories.website_repository import WebsiteRepository
from app.core.response import SuccessResponseModel

router = APIRouter()


@router.get("/", response_model=SuccessResponseModel[WebsiteResponse])
async def get_website_config(db: AsyncSession = Depends(get_db)):
    """
    Get the current global website scraping configuration.
    """
    website = await WebsiteRepository(db).get()
    return SuccessResponseModel(data=website)


@router.patch("/", response_model=SuccessResponseModel[WebsiteResponse])
async def update_website_config(
    item_in: WebsiteUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update specific fields of the website configuration.
    Only fields sent in the JSON body will be updated.
    """
    website = await WebsiteRepository(db).update(id=1, item_in=item_in)
    return SuccessResponseModel(data=website)
