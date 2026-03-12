import asyncio
import hashlib
import re
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from app.core.logging import logger
from app.schemas.content_scraper import ScrapeConfig, ExtractedContent, PageMetadata
from app.utils.url_utils import normalize_url
from typing import Callable, Awaitable

ProgressCallback = Callable[[str], Awaitable[None]]

URL_PATTERN = re.compile(r"^https?://[^\s]+$")


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_url(url: str) -> bool:
    if not URL_PATTERN.match(url):
        return False
    parsed = urlparse(url)
    return bool(parsed.scheme in ("http", "https") and parsed.netloc)


def _create_browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_type="chromium",
        text_mode=True,
        light_mode=True,
        user_agent_mode="random",
        user_agent_generator_config={
            "browsers": ["Chrome", "Firefox", "Edge", "Safari"],
            "os": ["Windows", "macOS", "Linux"],
        },
    )


def _create_crawler_config(timeout: int) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        excluded_tags=[
            "nav",
            "footer",
            "header",
            "script",
            "style",
            "noscript",
            "form",
        ],
        remove_forms=True,
        scan_full_page=True,
        process_iframes=True,
        remove_overlay_elements=True,
        simulate_user=True,
        wait_for_images=False,
        wait_until="networkidle",
        page_timeout=timeout * 1000,
        wait_for="body",
        wait_for_timeout=timeout * 1000,
        delay_before_return_html=0.3,
        mean_delay=0.4,
        max_range=0.6,
        semaphore_count=6,
        cache_mode=CacheMode.DISABLED,
    )


async def scrape_content(
    urls: list[str],
    config: ScrapeConfig,
    progress_callback: ProgressCallback,
) -> list[ExtractedContent]:
    if not urls:
        return []

    valid_urls = [url for url in urls if validate_url(url)]
    if not valid_urls:
        logger.warning("No valid URLs provided")
        return []

    # Create browser and crawler configs
    browser_config = _create_browser_config()
    crawler_config = _create_crawler_config(timeout=config.timeout_seconds)

    # Initialize variables
    url_to_result: dict[str, dict] = {}
    pending_urls = valid_urls.copy()
    crawler = None

    try:
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.start()

        for attempt in range(config.max_retries):
            failed_urls = [
                url
                for url in pending_urls
                if url not in url_to_result or not url_to_result[url]["success"]
            ]

            # If all URLs have been processed successfully, break out of the loop
            if not failed_urls:
                break

            if attempt > 0:
                # Only report retries — first attempt is reported by the caller
                await progress_callback(
                    f"Retrying {len(failed_urls)} failed URLs (attempt {attempt + 1}/{config.max_retries})",
                )
                logger.info(
                    f"Attempt {attempt + 1}/{config.max_retries}: {len(failed_urls)} URLs remaining"
                )

            raw_results = await crawler.arun_many(
                urls=failed_urls, config=crawler_config
            )
            results = list(raw_results) if raw_results else []

            for result in results:
                url_to_result[result.url] = {
                    "success": result.success,
                    "markdown": result.markdown or "",
                    "metadata": dict(result.metadata) if result.metadata else {},
                    "error_message": result.error_message,
                    "status_code": result.status_code,
                }

            await asyncio.sleep(config.delay_between_batches)

    except asyncio.CancelledError:
        logger.warning("Scraping task was cancelled")
        raise
    except Exception as e:
        logger.exception(f"Scraping failed with error: {str(e)}")
    finally:
        if crawler:
            try:
                await crawler.close()
            except Exception as e:
                logger.warning(f"Error closing crawler: {str(e)}")

    results_list = []
    for url, data in url_to_result.items():
        # Determine error type based on status code and error message
        error_type, error_message = None, data.get("error_message")
        if not data["success"] and error_message:
            status_code = data.get("status_code")
            if status_code == 429:
                error_type = "rate_limit"
            elif status_code in (401, 403):
                error_type = "auth"
            elif status_code == 408 or "timeout" in error_message.lower():
                error_type = "timeout"
            else:
                error_type = "unknown"

        results_list.append(
            ExtractedContent(
                url=url,
                resource_id=0,
                content_hash=compute_content_hash(data["markdown"]),
                markdown=data["markdown"],
                metadata=PageMetadata(**data.get("metadata", {})),
                success=data["success"],
                error_type=error_type,
                error_message=error_message,
            )
        )

    return results_list


async def run_content_scraper(
    progress_callback: ProgressCallback,
    config: ScrapeConfig | None = None,
) -> tuple[list[ExtractedContent], int, int]:
    if config is None:
        config = ScrapeConfig()

    from app.repositories.scraped_resources_repository import ScrapedResourcesRepository
    from app.core.database import get_session

    progress_callback("Starting content scraper...")

    # Get URLs and IDs from the database
    async with get_session() as session:
        repo = ScrapedResourcesRepository(session=session)
        urls_and_ids: list[tuple[str, int]] = await repo.get_urls_and_ids()

    if not urls_and_ids:
        await progress_callback("No URLs found to scrape")
        logger.info("No URLs found to scrape")
        return [], 0, 0

    progress_callback(f"Found {len(urls_and_ids)} URLs to scrape")
    logger.info(f"Found {len(urls_and_ids)} URLs to scrape")

    # Create a mapping of normalized URLs to resource IDs
    url_to_resource_id = {normalize_url(url): rid for url, rid in urls_and_ids}
    logger.info(f"Found {len(urls_and_ids)} URLs to scrape")

    results: list[ExtractedContent] = []
    # Split URLs into batches
    batches = [
        urls_and_ids[i : i + config.batch_size]
        for i in range(0, len(urls_and_ids), config.batch_size)
    ]

    async def process_batch(
        batch: list[tuple[str, int]], batch_idx: int
    ) -> list[ExtractedContent]:
        logger.info(
            f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} URLs)"
        )
        batch_urls = [normalize_url(url) for url, _ in batch]
        scraped = await scrape_content(batch_urls, config, progress_callback)

        # Assign resource IDs to scraped content
        for content in scraped:
            content.resource_id = url_to_resource_id.get(content.url, 0)

        await progress_callback(
            f"Completed batch {batch_idx + 1}/{len(batches)}: Scraped {len(scraped)} items"
        )

        return [c for c in scraped if c.resource_id]

    max_concurrent_batches = 4

    # Process batches concurrently
    for batch_idx in range(0, len(batches), max_concurrent_batches):
        batch_chunk = batches[batch_idx : batch_idx + max_concurrent_batches]
        chunk_results = await asyncio.gather(
            *(
                process_batch(batch, batch_idx + i)
                for i, batch in enumerate(batch_chunk)
            ),
            return_exceptions=True,
        )

        # Aggregate results
        for i, batch_result in enumerate(chunk_results):
            if isinstance(batch_result, Exception):
                logger.error(f"Batch {batch_idx + i + 1} failed: {str(batch_result)}")
            elif isinstance(batch_result, list):
                results.extend(batch_result)

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    logger.info(f"Scraping complete: {len(successful)} succeeded, {len(failed)} failed")

    return successful, len(successful), len(failed)
