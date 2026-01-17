from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ScrapedContent(Base):
    __tablename__ = "scraped_content"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking to ScrapedResource
    resource_id = Column(
        Integer,
        ForeignKey("scraped_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    url = Column(String(2048), nullable=False, default="")

    content = Column(Text, nullable=False)

    content_hash = Column(String(128), nullable=False, index=True)

    meta_data = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Ensure content_hash is unique
    __table_args__ = (UniqueConstraint("content_hash", name="unique_content_hash"),)

    # Relationships
    resource = relationship("ScrapedResource", back_populates="contents")
