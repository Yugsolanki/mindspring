from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ScrapedContent(Base):
    __tablename__ = "scraped_content"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key linking to ScrapedResource
    resource_id = Column(Integer, ForeignKey("scraped_resources.id"), index=True)

    content = Column(String)  # The actual text content extracted from the resource

    # Vector Embeddings
    dense_embeddings = Column(
        ARRAY(Float)
    )  # For dense vector search (e.g., cosine similarity)
    sparse_embeddings = Column(ARRAY(Float))  # For hybrid search (BM25 or Splade)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now()
    )

    # Relationships
    resource = relationship("ScrapedResource", back_populates="contents")
