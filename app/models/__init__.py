from app.models.website import Website
from app.models.resource import ScrapedResource
from app.models.content import ScrapedContent

# This allows you to just do: from app.models import Website, ScrapedResource
__all__ = ["Website", "ScrapedResource", "ScrapedContent"]
