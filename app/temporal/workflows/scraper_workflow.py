from dataclasses import dataclass

from temporalio import workflow
from temporalio.exceptions import ActivityError

# Import activity functions and options
from app.temporal.activities.link_scraper_activity import (
    SCRAPE_LINKS_ACTIVITY_OPTIONS,
    scrape_links_activity,
    LinkScraperResult,
)
from app.temporal.activities.store_scraped_links_activity import (
    STORE_LINKS_ACTIVITY_OPTIONS,
    store_scraped_links_activity,
    StoreLinksInput,
)


@dataclass
class ScraperWorkflowResult:
    """Result of the complete scraper workflow"""

    links_scraper: int
    links_stored: int
    duplicates_skipped: int
    message: str


@workflow.defn
class LinkScraperWorkflow:
    """
    Workflow that orchestrates the link scraping and storage process
    - Singleton execution (via workflow ID)
    - Retries with backoff
    - Heartbeat monitoring
    - State persistence
    """

    def __init__(self):
        self._is_cancelled = False

    @workflow.run
    async def run(self):
        """
        Execute the following scraping pipeline steps:
        1. Scrape links (Activity)
        2. Store scraped links (Activity)
        """
        workflow.logger.info("Starting LinkScraperWorkflow...")

        try:
            # Step 1: Scrape Links
            scraper_result: LinkScraperResult = await workflow.execute_activity(
                scrape_links_activity,
                **SCRAPE_LINKS_ACTIVITY_OPTIONS,
            )

            if self._is_cancelled:
                workflow.logger.info("LinkScraperWorkflow cancelled")
                return ScraperWorkflowResult(
                    links_scraper=scraper_result.count,
                    links_stored=0,
                    duplicates_skipped=0,
                    message="LinkScraperWorkflow cancelled",
                )

            # Step 2: Store Links
            if scraper_result.links:
                store_result = await workflow.execute_activity(
                    store_scraped_links_activity,
                    StoreLinksInput(links=scraper_result.links),
                    **STORE_LINKS_ACTIVITY_OPTIONS,
                )

                workflow.logger.info(
                    f"LinkScraperWorkflow finished: {store_result.message}"
                )
                return ScraperWorkflowResult(
                    links_scraper=scraper_result.count,
                    links_stored=store_result.new_links_stored,
                    duplicates_skipped=store_result.duplicates_skipped,
                    message=store_result.message,
                )
            else:
                workflow.logger.info("No links found to store")
                return ScraperWorkflowResult(
                    links_scraper=scraper_result.count,
                    links_stored=0,
                    duplicates_skipped=0,
                    message="No links found to store",
                )
        except ActivityError as e:
            workflow.logger.info(f"Activity failed after retries: {e}")
            raise

    @workflow.signal
    async def cancel(self):
        """Signal to cancel execution gracefully"""
        self._is_cancelled = True
        workflow.logger.info("LinkScraperWorkflow canceled")
