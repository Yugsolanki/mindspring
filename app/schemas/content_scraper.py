from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ScrapeConfig(BaseModel):
    batch_size: int = Field(default=20, ge=1, le=100, description="URLs per batch")
    max_retries: int = Field(default=3, ge=0, le=10, description="Retries per URL")
    timeout_seconds: int = Field(default=45, ge=10, le=300, description="Page timeout")
    delay_between_batches: float = Field(
        default=0.5, ge=0.0, description="Batch cooldown"
    )

    model_config = ConfigDict(frozen=True)


class PageMetadata(BaseModel):
    title: str = Field(default="Untitled", description="Page title")
    description: Optional[str] = Field(default=None, description="Meta description")
    source_url: str = Field(default="Unknown Source", description="Source URL")
    accessed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    language: Optional[str] = Field(default=None, description="Detected language")
    word_count: Optional[int] = Field(default=None, description="Word count")


class ExtractedContent(BaseModel):
    url: str
    resource_id: int
    content_hash: str
    markdown: str
    metadata: PageMetadata
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
