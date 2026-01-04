from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from app.core.database import engine, SessionLocal
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.models import Website


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MindSpring API is starting up...")

    # Verification: Check DB connection (Optional but recommended)
    try:
        # Just a sanity check or table creation if not using Alembic strictly
        logger.info("Verifying Database connection...")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e

    # INITIALIZE SINGLETON WEBSITE CONFIG
    async with SessionLocal() as session:
        try:
            logger.info("Checking for default Website Configuration...")

            result = await session.execute(select(Website).where(Website.id == 1))
            website = result.scalars().first()

            if not website:
                logger.info("No config found. Creating Default Website (ID=1)...")
                new_website = Website(
                    id=1,
                    title="MindSpring Default",
                    description="Initial default configuration",
                )
                session.add(new_website)
                await session.commit()
                logger.info("Default Website Configuration created successfully.")
            else:
                logger.info(
                    f"Website Configuration loaded: {website.domain} (ID: {website.id})"
                )
        except Exception as e:
            logger.error(f"Error initializing singleton Website config: {e}")
            raise e

    yield  # <--------- Application runs here

    # Shutdown Logic
    logger.info("MindSpring API is shutting down...")

    # Gracefully close the Async Database Engine
    logger.info("Disposing Database Engine...")
    await engine.dispose()

    logger.info("Cleanup complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()

# If running directly for debugging
if __name__ == "__main__":
    import uvicorn

    # You can access docs at http://localhost:8000/docs
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
