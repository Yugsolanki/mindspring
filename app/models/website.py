from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ARRAY,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Website(Base):
    __tablename__ = "websites"

    # Enforce that the ID must always be 1.
    # This prevents creating rows with id=2, id=3, etc.
    __table_args__ = (CheckConstraint("id = 1", name="singleton_website_constraint"),)

    id = Column(Integer, primary_key=True, server_default="1")
    domain = Column(
        String, unique=True, index=True, default="example.com", nullable=False
    )
    title = Column(String)
    description = Column(String)

    # Celery Config
    timezone = Column(String(50), default="UTC")

    # URL Management
    white_listed_domain = Column(ARRAY(String), default=list)
    black_listed_domain = Column(ARRAY(String), default=list)
    white_listed_path_patterns = Column(ARRAY(String), default=list)
    black_listed_path_patterns = Column(ARRAY(String), default=list)

    # Scraping Rules
    respect_robots = Column(Boolean, default=False)
    max_concurrent = Column(Integer, default=8)
    playwright_timeout = Column(Integer, default=30)
    timeout = Column(Integer, default=15)
    max_retries = Column(Integer, default=3)
    max_depth = Column(Integer, default=100)
    rate_limiting_delay = Column(Integer, default=2)
    user_agents = Column(
        ARRAY(String), default=["Mozilla/5.0 (compatible; MindSpringBot/1.0)"]
    )
    scraping_schedule = Column(String, default="* * * * *")  # Standard cron format

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    # This allows you to access all resources belonging to this website
    resources = relationship(
        "ScrapedResource", back_populates="website", cascade="all, delete-orphan"
    )
