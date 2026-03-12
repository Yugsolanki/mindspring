from dataclasses import dataclass

from temporalio import workflow
from temporalio.exceptions import ActivityError

from app.temporal.activities.content_scraper_activity import (
    CONTENT_SCRAPER_ACTIVITY_OPTIONS,
    content_scraper_activity,
    ContentScraperResult,
)
from app.temporal.activities.store_content_activity import (
    STORE_CONTENT_ACTIVITY_OPTIONS,
    store_content_activity,
    StoreContentResult,
)


@dataclass
class ContentScraperWorkflowResult:
    """Result of the complete content scraper workflow"""

    content_scraped: int
    content_stored: int
    duplicates_skipped: int
    updated_count: int
    message: str


@workflow.defn
class ContentScraperWorkflow:
    def __init__(self):
        self._is_cancelled = False

    @workflow.run
    async def run(self):
        workflow.logger.info("Starting ContentScraperWorkflow...")

        try:
            # Step 1: Scrape Content
            scraper_result: ContentScraperResult = await workflow.execute_activity(
                content_scraper_activity,
                **CONTENT_SCRAPER_ACTIVITY_OPTIONS,
            )

            if self._is_cancelled:
                workflow.logger.info("ContentScraperWorkflow cancelled")
                return ContentScraperWorkflowResult(
                    content_scraped=len(scraper_result.content_list),
                    content_stored=0,
                    duplicates_skipped=0,
                    updated_count=0,
                    message="ContentScraperWorkflow cancelled",
                )

            if scraper_result.content_list:
                # Step 2: Store Scraped Content
                # The activity expects a StoreContentInput dataclass, not a raw list.  Build
                # the input explicitly (or pass as keyword) to avoid Temporal decoding errors.
                from app.temporal.activities.store_content_activity import (
                    StoreContentInput,
                )

                store_input = StoreContentInput(
                    content_list=scraper_result.content_list
                )
                store_result: StoreContentResult = await workflow.execute_activity(
                    store_content_activity,
                    store_input,
                    **STORE_CONTENT_ACTIVITY_OPTIONS,
                )

                workflow.logger.info(
                    f"ContentScraperWorkflow finished: {store_result.message}"
                )
                return ContentScraperWorkflowResult(
                    content_scraped=len(scraper_result.content_list),
                    content_stored=store_result.content_stored,
                    duplicates_skipped=store_result.content_skipped,
                    updated_count=store_result.content_updated,
                    message=store_result.message,
                )
            else:
                workflow.logger.info("No content found to store")
                return ContentScraperWorkflowResult(
                    content_scraped=0,
                    content_stored=0,
                    duplicates_skipped=0,
                    updated_count=0,
                    message="No content found to store",
                )
        except ActivityError as e:
            workflow.logger.info(f"Activity failed after retries: {e}")
            raise

    @workflow.signal
    def cancel(self):
        workflow.logger.info("Received cancel signal for ContentScraperWorkflow")
        self._is_cancelled = True
