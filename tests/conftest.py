import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models.website import Website
from app.repositories.website_repository import WebsiteRepository
from app.main import app


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def async_client(async_session) -> AsyncGenerator[AsyncClient, None]:
    """Create async client for testing API endpoints."""

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def website_repository(async_session) -> WebsiteRepository:
    """Create website repository instance."""
    return WebsiteRepository(async_session)


@pytest_asyncio.fixture
async def sample_website(async_session) -> Website:
    """Create a sample website in the database."""
    website = Website(
        id=1,
        domain="example.com",
        title="Test Website",
        description="A test website",
        timezone="UTC",
        white_listed_domain=["allowed.com"],
        black_listed_domain=["blocked.com"],
        white_listed_path_patterns=[r"^/api/.*"],
        black_listed_path_patterns=[r"^/admin/.*"],
        respect_robots=True,
        max_concurrent=10,
        playwright_timeout=30,
        timeout=15,
        max_retries=3,
        max_depth=100,
        rate_limiting_delay=2,
        user_agents=["Mozilla/5.0 (compatible; MindSpringBot/1.0)"],
        scraping_schedule="0 * * * *",
    )
    async_session.add(website)
    await async_session.commit()
    await async_session.refresh(website)
    return website


@pytest.fixture
def valid_website_data() -> dict:
    """Return valid website data for testing."""
    return {
        "domain": "testsite.com",
        "title": "Test Site",
        "description": "A test site description",
        "timezone": "America/New_York",
        "white_listed_domain": ["partner.com"],
        "black_listed_domain": ["spam.com"],
        "white_listed_path_patterns": [r"^/public/.*"],
        "black_listed_path_patterns": [r"^/private/.*"],
        "respect_robots": True,
        "max_concurrent": 5,
        "playwright_timeout": 60,
        "timeout": 30,
        "max_retries": 5,
        "max_depth": 50,
        "rate_limiting_delay": 5,
        "user_agents": ["CustomBot/1.0"],
        "scraping_schedule": "0 0 * * *",
    }


@pytest.fixture
def minimal_website_data() -> dict:
    """Return minimal valid website data."""
    return {"domain": "minimal.com"}


@pytest.fixture
def invalid_website_data_samples() -> list:
    """Return various invalid website data samples."""
    return [
        {"domain": "invalid domain with spaces"},
        {"domain": "nodot"},
        {"domain": ""},
        {"timezone": "Invalid/Timezone"},
        {"max_concurrent": 0},
        {"max_concurrent": 101},
        {"playwright_timeout": 0},
        {"playwright_timeout": 121},
        {"timeout": 0},
        {"timeout": 121},
        {"max_retries": -1},
        {"max_retries": 11},
        {"max_depth": 0},
        {"max_depth": 1001},
        {"rate_limiting_delay": -1},
        {"rate_limiting_delay": 61},
        {"user_agents": []},
        {"user_agents": ["ab"]},  # Too short
        {"scraping_schedule": "invalid cron"},
        {"white_listed_path_patterns": ["[invalid regex"]},
    ]
