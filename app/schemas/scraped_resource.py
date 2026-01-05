from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from datetime import datetime


class ScrapedResourceBase(BaseModel):
    website_id: int = Field(
        ..., description="ID of the website this resource belongs to"
    )
    url: str = Field(..., description="The full URL of the resource")
    content_type: Optional[str] = Field(
        None, description="MIME type (e.g., 'text/html')"
    )
    scrape_status: str = Field(
        default="pending",
        description="Current status: pending, processing, completed, failed",
    )

    class Config:
        from_attributes = True


class ScrapedResourceCreate(ScrapedResourceBase):
    """
    Schema for creating a new ScrapedResource.
    """

    pass


class ScrapedResourceUpdate(BaseModel):
    """
    Schema for updating a ScrapedResource (e.g., changing status).
    """

    url: Optional[str] = None
    content_type: Optional[str] = None
    scrape_status: Optional[str] = None


class ScrapedResourceResponse(ScrapedResourceBase):
    """
    Standard Schema for returning ScrapedResource data.
    """

    id: int
    last_scraped: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScrapedResourceWithContents(ScrapedResourceResponse):
    """
    Extended Schema that includes the nested 'contents' relationship.
    Useful when you need the resource metadata AND its associated text content.
    """

    contents: List["ScrapedContentResponse"] = []


# Perform the actual import AFTER the class is defined.
# This resolves the circular dependency (Class defined -> Import -> Rebuild).
from .scraped_content import ScrapedContentResponse

# Update the forward references in the model
ScrapedResourceWithContents.model_rebuild()
