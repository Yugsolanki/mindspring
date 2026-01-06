from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, HttpUrl, model_validator
from datetime import datetime

ScrapedStatus = Literal["pending", "processing", "completed", "failed"]

AllowedContentTypes = Literal[
    "text/html",
    "text/plain",
    "application/json",
    "application/xml",
    "application/xhtml+xml",
    "application/rss+xml",
    "application/atom+xml",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
]


class ScrapedResourceBase(BaseModel):
    website_id: int = Field(
        ..., description="ID of the website this resource belongs to", ge=1, le=1
    )
    url: HttpUrl = Field(
        ..., description="The full URL of the resource", max_length=2048
    )
    content_type: Optional[AllowedContentTypes] = Field(
        None, description="MIME type (e.g., 'text/html')"
    )
    scrape_status: ScrapedStatus = Field(
        default="pending",
        description="Current status: pending, processing, completed, failed",
    )

    model_config = ConfigDict(from_attributes=True)


class ScrapedResourceCreate(ScrapedResourceBase):
    """
    Schema for creating a new ScrapedResource.
    """

    pass


class ScrapedResourceUpdate(BaseModel):
    """
    Schema for updating a ScrapedResource (e.g., changing status).
    """

    url: Optional[HttpUrl] = Field(None, max_length=2048)
    content_type: Optional[AllowedContentTypes] = None
    scrape_status: Optional[ScrapedStatus] = None

    # ==================
    # Model Validators
    # ==================
    @model_validator(mode="after")
    def ensure_not_empty(self):
        if not any(value is not None for value in self.__dict__.values()):
            raise ValueError("At least one field must be provided for update")
        return self


class ScrapedResourceResponse(ScrapedResourceBase):
    """
    Standard Schema for returning ScrapedResource data.
    """

    id: int = Field(..., frozen=True)
    # last_scraped is Optional cuz maybe it was never scraped only the url is stored
    last_scraped: Optional[datetime] = Field(None, frozen=True)
    created_at: datetime = Field(..., frozen=True)
    updated_at: datetime = Field(..., frozen=True)

    model_config = ConfigDict(from_attributes=True)


class ScrapedResourceWithContents(ScrapedResourceResponse):
    """
    Extended Schema that includes the nested 'contents' relationship.
    Useful when you need the resource metadata AND its associated text content.
    """

    contents: List["ScrapedContentResponse"] = Field(default_factory=list)


# Perform the actual import AFTER the class is defined.
# This resolves the circular dependency (Class defined -> Import -> Rebuild).
from .scraped_content import ScrapedContentResponse  # noqa

# Update the forward references in the model
ScrapedResourceWithContents.model_rebuild()
