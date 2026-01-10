from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ScrapedResource(Base):
    __tablename__ = "scraped_resources"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking to Website
    website_id = Column(Integer, ForeignKey("websites.id"), index=True)

    url = Column(String, index=True)
    content_type = Column(String)  # e.g., 'text/html', 'application/pdf'
    scrape_status = Column(
        String, default="pending", index=True
    )  # pending, processing, completed, failed

    last_scraped = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    website = relationship("Website", back_populates="resources")
    # A resource can have one (or multiple) content blocks
    contents = relationship(
        "ScrapedContent", back_populates="resource", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("url", "website_id", name="scraped_resource_url_website_id"),
    )
