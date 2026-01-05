from fastapi import APIRouter
from app.api.v1.endpoints import health, website, scraped_resource, scraped_content

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["System"])
api_router.include_router(website.router, prefix="/website", tags=["Configuration"])
api_router.include_router(
    scraped_resource.router, prefix="/resources", tags=["Scraping Resources"]
)
api_router.include_router(
    scraped_content.router, prefix="/content", tags=["Scraped Content"]
)
