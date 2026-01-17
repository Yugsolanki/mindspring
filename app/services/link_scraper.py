from libs.TurboScraper.api_scraper import (
    AsyncParallelWebScraper,
    ScraperConfig,
    ScrapeRequest,
)
from app.schemas.website import WebsiteResponse
from app.core.logging import logger
from app.utils.mimetypes import is_allowed_content_type
from app.utils.url_utils import normalize_url
from app.core.response import SuccessResponseModel, ErrorResponseModel


async def create_scraper(config: WebsiteResponse):
    """
    Create scraper instance
    """
    scraper = AsyncParallelWebScraper(
        config=ScraperConfig(
            max_concurrent=config.max_concurrent,
            timeout=config.timeout,
            playwright_timeout=config.playwright_timeout,
            max_retries=config.max_retries,
            max_depth=config.max_depth,
            rate_limit_delay=config.rate_limiting_delay,
            respect_robots=config.respect_robots,
            user_agents=config.user_agents,
        )
    )

    scraper.add_to_whitelist(
        domain=config.white_listed_domain, paths=config.white_listed_path_patterns
    )
    scraper.add_to_blacklist(
        domain=config.black_listed_domain, paths=config.black_listed_path_patterns
    )

    await scraper.initialize()

    logger.info("Scraper initialized successfully")

    return scraper


async def run_scraper():
    """
    Run scraper to scrape website
    """
    from app.core.loaders import load_website
    from app.workers.store_scraped_links import store_scraped_links

    config: WebsiteResponse = await load_website()
    scraper = await create_scraper(config)

    try:
        logger.info(f"Scraping website: {config.domain}")
        scraped_links, external_links = await scraper.scrape_website(
            request=ScrapeRequest(start_url=config.domain)
        )
    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        return ErrorResponseModel(
            message="Error scraping website",
            error=str(e),
        ).model_dump_json()
    finally:
        await scraper.close()

    # Store scraped links
    # filter external links with allowed content types (images, videos, pdfs, docs, etc.)
    # even if from different domain, they will be scraped
    all_links = list(scraped_links) + [
        link for link in external_links if is_allowed_content_type(link)
    ]
    # normalize URLs for consistent matching
    all_links = [normalize_url(link) for link in all_links]
    # remove duplicates
    all_links = list(dict.fromkeys(all_links))

    store_scraped_links.delay(all_links)

    return SuccessResponseModel(
        message="Links scraped successfully",
        data={
            "links": all_links,
        },
    ).model_dump_json()
