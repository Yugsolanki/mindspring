from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from app.core.database import engine
from contextlib import asynccontextmanager


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
