from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
import re
from croniter import croniter
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# Regex for validating domain
DOMAIN_REGEX = re.compile(r"^(https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()
    return domain.rstrip("/")


# Define the default generator as a standalone function
def get_default_user_agents() -> List[str]:
    return ["Mozilla/5.0 (compatible; MindSpringBot/1.0)"]


class WebsiteBase(BaseModel):
    domain: str = Field(
        default="example.com",
        description="The primary domain of the website",
        max_length=255,
    )
    title: Optional[str] = Field(
        default=None, description="The title of the website", max_length=255
    )
    description: Optional[str] = Field(
        default=None, description="The description of the website", max_length=500
    )

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

    # Celery Config
    timezone: str = Field(default="UTC", description="Timezone for Celery")

    # Scraping Rules
    respect_robots: bool = Field(
        default=False, description="Whether to respect robots.txt"
    )
    max_concurrent: int = Field(
        default=8, ge=1, le=100, description="Max concurrent requests"
    )
    playwright_timeout: int = Field(
        default=30, ge=1, le=120, description="Playwright timeout in seconds"
    )
    timeout: int = Field(
        default=15, ge=1, le=120, description="Request timeout in seconds"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")
    max_depth: int = Field(default=100, ge=1, le=1000, description="Max crawl depth")
    rate_limiting_delay: int = Field(
        default=2, ge=0, le=60, description="Delay between requests in seconds"
    )
    user_agents: List[str] = Field(
        default_factory=get_default_user_agents,
        description="List of user agents to rotate",
        min_length=1,
        max_length=50,
    )
    scraping_schedule: str = Field(
        default="* * * * *", description="Cron schedule for scraping"
    )

    # ===================
    # Field Validators
    # ===================
    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    @field_validator("domain", mode="before")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = normalize_domain(v)
        if not DOMAIN_REGEX.match(v):
            raise ValueError("Invalid domain format")
        return v

    @field_validator("white_listed_domain", "black_listed_domain", mode="before")
    @classmethod
    def validate_domain_lists(cls, domains: List[str]) -> List[str]:
        # Validate that the input is a list
        if not isinstance(domains, list):
            raise ValueError("Must be a list of domains")

        # Validate that all domains are valid
        cleaned = []
        for d in domains:
            d = normalize_domain(d)
            if not DOMAIN_REGEX.match(d):
                raise ValueError(f"Invalid domain in list: {d}")
            cleaned.append(d)
        return cleaned

    @field_validator("white_listed_path_patterns", "black_listed_path_patterns")
    @classmethod
    def validate_regex_patterns(cls, patterns: List[str]) -> List[str]:
        if not isinstance(patterns, list):
            raise ValueError("Must be a list of regex patterns")

        # Validate that all regex patterns are valid
        for p in patterns:
            try:
                re.compile(p)
            except re.error:
                raise ValueError(f"Invalid regex pattern: {p}")
        return patterns

    @field_validator("scraping_schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        if not croniter.is_valid(v):
            raise ValueError("Invalid cron expression")
        return v

    @field_validator("user_agents")
    @classmethod
    def validate_user_agents(cls, agents: List[str]) -> List[str]:
        if not isinstance(agents, list):
            raise ValueError("Must be a list of user-agents")

        if not all(isinstance(a, str) and len(a) >= 5 for a in agents):
            raise ValueError("Each user-agent must be a non-empty string")
        return agents

    # ========================
    # Cross-Field Validator
    # ========================
    @model_validator(mode="after")
    def check_whitelist_blacklist_config(self):
        overlap = set(self.white_listed_domain) & set(self.black_listed_domain)
        if overlap:
            raise ValueError(
                f"Domains cannot be both whitelisted and blacklisted: {overlap}"
            )

        overlap_paths = set(self.white_listed_path_patterns) & set(
            self.black_listed_path_patterns
        )
        if overlap_paths:
            raise ValueError(
                f"Path patterns cannot be both whitelisted and blacklisted: {overlap_paths}"
            )

        return self

    # This allows Pydantic to read data even if it is passed as a standard dict
    # and not an object with attributes.
    model_config = ConfigDict(from_attributes=True)


class WebsiteCreate(WebsiteBase):
    """
    Schema for creating a new Website configuration.
    """

    # Inheriting all fields from WebsiteBase.
    pass


class WebsiteUpdate(BaseModel):
    """
    Schema for updating an existing Website configuration.
    All fields are optional to allow partial updates.
    """

    # Using 'Optional' for all fields to support PATCH requests (partial updates)
    domain: Optional[str] = Field(default=None, max_length=255)
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)

    white_listed_domain: Optional[List[str]] = None
    black_listed_domain: Optional[List[str]] = None
    white_listed_path_patterns: Optional[List[str]] = None
    black_listed_path_patterns: Optional[List[str]] = None

    timezone: Optional[str] = None

    respect_robots: Optional[bool] = None
    max_concurrent: Optional[int] = Field(default=None, ge=1, le=100)
    playwright_timeout: Optional[int] = Field(default=None, ge=1, le=120)
    timeout: Optional[int] = Field(default=None, ge=1, le=120)
    max_retries: Optional[int] = Field(default=None, ge=0, le=10)
    max_depth: Optional[int] = Field(default=None, ge=1, le=1000)
    rate_limiting_delay: Optional[int] = Field(default=None, ge=0, le=60)
    user_agents: Optional[List[str]] = None
    scraping_schedule: Optional[str] = None

    # ====================
    # Field Validators
    # ====================
    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:  # If the timezone is present
            try:
                ZoneInfo(v)
            except ZoneInfoNotFoundError:
                raise ValueError(f"Invalid timezone: {v}")
            return v
        return v

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:  # If the domain is present
            v = normalize_domain(v)
            if not DOMAIN_REGEX.match(v):  # Validate the domain format
                raise ValueError("Invalid domain format")
            return v
        return v

    @field_validator("white_listed_domain", "black_listed_domain", mode="before")
    @classmethod
    def normalize_domain_lists_if_present(
        cls, domains: Optional[List[str]]
    ) -> Optional[List[str]]:
        if domains is not None:  # If the domain list is present
            # Validate that the input is a list
            if not isinstance(domains, list):
                raise ValueError("Must be a list of domains")

            # Clean and validate each domain
            cleaned = []
            for d in domains:
                d = normalize_domain(d)
                if not DOMAIN_REGEX.match(d):
                    raise ValueError("Invalid domain format")
                cleaned.append(d)
            return cleaned
        return domains

    @field_validator("white_listed_path_patterns", "black_listed_path_patterns")
    @classmethod
    def validate_regex_patterns_if_present(
        cls, patterns: Optional[List[str]]
    ) -> Optional[List[str]]:
        if patterns is not None:
            if not isinstance(patterns, list):
                raise ValueError("Must be a list of regex patterns")

            # Validate each pattern
            for p in patterns:
                try:
                    re.compile(p)  # Validate the regex pattern
                except re.error:
                    raise ValueError(f"Invalid regex pattern: {p}")
            return patterns
        return patterns

    @field_validator("scraping_schedule")
    @classmethod
    def validate_cron_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not croniter.is_valid(v):  # Validate the cron expression
                raise ValueError("Invalid cron expression")
            return v
        return v

    @field_validator("user_agents")
    @classmethod
    def validate_user_agents_if_present(
        cls, agents: Optional[List[str]]
    ) -> Optional[List[str]]:
        if agents is not None:
            if not isinstance(agents, list):
                raise ValueError("Must be a list of user-agents")

            if not all(isinstance(a, str) and len(a) >= 5 for a in agents):
                raise ValueError("Each user-agent must be a non-empty string")
            return agents
        return agents

    # ========================
    # Cross-Field Validator
    # ========================
    @model_validator(mode="after")
    def check_whitelist_blacklist_config_if_present(self):
        # Validate whitelist and blacklist domains are present and don't overlap
        if (
            self.white_listed_domain is not None
            and self.black_listed_domain is not None
        ):
            overlap = set(self.white_listed_domain) & set(self.black_listed_domain)
            if overlap:
                raise ValueError(
                    f"Domains cannot be both whitelisted and blacklisted: {overlap}"
                )

        # Validate whitelist and blacklist path patterns are present and don't overlap
        if (
            self.white_listed_path_patterns is not None
            and self.black_listed_path_patterns is not None
        ):
            overlap_paths = set(self.white_listed_path_patterns) & set(
                self.black_listed_path_patterns
            )
            if overlap_paths:
                raise ValueError(
                    f"Path patterns cannot be both whitelisted and blacklisted: {overlap_paths}"
                )
        return self

    # ==================
    # Model Validators
    # ==================
    @model_validator(mode="after")
    def ensure_not_empty(self):
        if not any(value is not None for value in self.__dict__.values()):
            raise ValueError("At least one field must be provided for update")
        return self


class WebsiteResponse(WebsiteBase):
    """
    Schema for returning Website data via the API.
    Includes database-managed fields.
    """

    id: int = Field(..., frozen=True)
    created_at: datetime = Field(..., frozen=True)
    updated_at: datetime = Field(..., frozen=True)

    # This allows Pydantic to read data even if it is passed as a standard dict
    # and not an object with attributes.
    model_config = ConfigDict(from_attributes=True)
