from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime


class ScrapedContentBase(BaseModel):
    resource_id: int = Field(
        ...,
        ge=1,
        description="The ID of the parent ScrapedResource",
    )
    content: str = Field(..., description="The extracted text content")
    content_hash: str = Field(..., description="The hash of the content")
    meta_data: dict = Field(..., description="Metadata associated with the content")
    url: str = Field(default="", description="Source URL of the scraped content")

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
    content_hash: Optional[str] = None
    meta_data: Optional[dict] = None

    # ==================
    # Model Validators
    # ==================
    @model_validator(mode="after")
    def ensure_not_empty(self):
        if not any(v is not None for v in self.__dict__.values()):
            raise ValueError("At least one field must be provided for update")
        return self


class ScrapedContentResponse(ScrapedContentBase):
    """
    Schema for returning ScrapedContent data via the API.
    """

    id: int = Field(..., frozen=True)
    created_at: datetime = Field(..., frozen=True)
    updated_at: datetime = Field(..., frozen=True)

    model_config = ConfigDict(from_attributes=True)
