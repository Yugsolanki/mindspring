from app.models.website import Website
from app.models.scraped_resource import ScrapedResource
from app.models.scraped_content import ScrapedContent
from app.core.database import Base

# This allows you to just do: from app.models import Website, ScrapedResource
__all__ = ["Base", "Website", "ScrapedResource", "ScrapedContent"]
