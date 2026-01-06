from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
import math


class ScrapedContentBase(BaseModel):
    resource_id: int = Field(
        ..., ge=1, description="The ID of the parent ScrapedResource"
    )
    content: Optional[str] = Field(None, description="The extracted text content")

    # Vector Embeddings (Optional because they might be generated later)
    dense_embeddings: Optional[List[float]] = Field(
        default=None,
        description="Dense vector embeddings for similarity search",
        max_length=4096,
    )
    sparse_embeddings: Optional[List[float]] = Field(
        default=None,
        description="Sparse vector embeddings for hybrid search",
        max_length=4096,
    )

    # ====================
    # Field Validators
    # ====================
    @field_validator("dense_embeddings", "sparse_embeddings")
    @classmethod
    def validate_embeddings(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is None:
            return v
        if not all(isinstance(x, (float, int)) and math.isfinite(x) for x in v):
            raise ValueError("Embeddings must be finite numeric values")
        return [float(x) for x in v]

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
    dense_embeddings: Optional[List[float]] = Field(
        None,
        max_length=4096,
    )
    sparse_embeddings: Optional[List[float]] = Field(
        None,
        max_length=4096,
    )

    # ====================
    # Field Validators
    # ====================
    @field_validator("dense_embeddings", "sparse_embeddings")
    @classmethod
    def validate_embeddings_if_present(
        cls, v: Optional[List[float]]
    ) -> Optional[List[float]]:
        if v is None:
            return v
        if not all(isinstance(x, (float, int)) and math.isfinite(x) for x in v):
            raise ValueError("Embeddings must be finite numeric values")
        return [float(x) for x in v]

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
