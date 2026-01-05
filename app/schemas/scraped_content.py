from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ScrapedContentBase(BaseModel):
    resource_id: int = Field(..., description="The ID of the parent ScrapedResource")
    content: Optional[str] = Field(None, description="The extracted text content")

    # Vector Embeddings (Optional because they might be generated later)
    dense_embeddings: Optional[List[float]] = Field(
        default=None, description="Dense vector embeddings for similarity search"
    )
    sparse_embeddings: Optional[List[float]] = Field(
        default=None, description="Sparse vector embeddings for hybrid search"
    )

    model_config = ConfigDict(from_attributes=True)


class ScrapedContentCreate(ScrapedContentBase):
    """
    Schema for creating a new ScrapedContent entry.
    """

    pass


class ScrapedContentUpdate(BaseModel):
    """
    Schema for updating existing content.
    All fields are optional to support partial updates.
    """

    content: Optional[str] = None
    dense_embeddings: Optional[List[float]] = None
    sparse_embeddings: Optional[List[float]] = None


class ScrapedContentResponse(ScrapedContentBase):
    """
    Schema for returning ScrapedContent data via the API.
    """

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
