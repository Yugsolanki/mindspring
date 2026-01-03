from fastapi import APIRouter
from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "active",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# db health check
@router.get("/db")
async def db_health_check():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"database": "connected"}
