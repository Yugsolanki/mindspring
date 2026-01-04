from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WebsiteBase(BaseModel):
    domain: str = Field(
        default="example.com", description="The primary domain of the website"
    )
    title: Optional[str] = None
    description: Optional[str] = None

    # URL Management
    white_listed_domain: List[str] = Field(
        default_factory=list, description="List of allowed domains"
    )
    black_listed_domain: List[str] = Field(
        default_factory=list, description="List of blocked domains"
    )
    white_listed_path_patterns: List[str] = Field(
        default_factory=list, description="Regex patterns for allowed paths"
    )
    black_listed_path_patterns: List[str] = Field(
        default_factory=list, description="Regex patterns for blocked paths"
    )

    # Scraping Rules
    respect_robots: bool = Field(
        default=False, description="Whether to respect robots.txt"
    )
    max_concurrent: int = Field(default=8, ge=1, description="Max concurrent requests")
    timeout: int = Field(default=15, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Max retry attempts")
    max_depth: int = Field(default=100, ge=1, description="Max crawl depth")
    rate_limiting_delay: int = Field(
        default=2, ge=0, description="Delay between requests in seconds"
    )
    user_agents: List[str] = Field(
        default=lambda: ["Mozilla/5.0 (compatible; MindSpringBot/1.0)"],
        description="List of user agents to rotate",
    )
    scraping_schedule: str = Field(
        default="* * * * *", description="Cron schedule for scraping"
    )

    class Config:
        # This allows Pydantic to read data even if it is passed as a standard dict
        # and not an object with attributes.
        from_attributes = True


class WebsiteCreate(WebsiteBase):
    """
    Schema for creating a new Website configuration.
    """

    # Inheriting all fields from WebsiteBase.
    pass


class WebsiteUpdate(WebsiteBase):
    """
    Schema for updating an existing Website configuration.
    All fields are optional to allow partial updates.
    """

    # Using 'Optional' for all fields to support PATCH requests (partial updates)
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    white_listed_domain: Optional[List[str]] = None
    black_listed_domain: Optional[List[str]] = None
    white_listed_path_patterns: Optional[List[str]] = None
    black_listed_path_patterns: Optional[List[str]] = None

    respect_robots: Optional[bool] = None
    max_concurrent: Optional[int] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    max_depth: Optional[int] = None
    rate_limiting_delay: Optional[int] = None
    user_agents: Optional[List[str]] = None
    scraping_schedule: Optional[str] = None


class WebsiteResponse(WebsiteBase):
    """
    Schema for returning Website data via the API.
    Includes database-managed fields.
    """

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
