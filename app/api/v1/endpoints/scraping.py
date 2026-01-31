from fastapi import APIRouter
from app.workers.content_scraper import content_scraper
from app.core.config import settings
from app.core.temporal_client import get_temporal_client
from app.temporal.workflows.scraper_workflow import LinkScraperWorkflow
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy

router = APIRouter()


@router.post("/links")
async def scrape_links():
    client: Client = await get_temporal_client()

    # Using a fixed workflow ID to ensure singleton execution
    workflow_id = "link-scraper-workflow-singleton"

    try:
        handle = await client.start_workflow(
            workflow=LinkScraperWorkflow,
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        )

        return {
            "message": "Link Scraper Workflow started",
            "workflow_id": handle.id,
            "run_id": handle.result_run_id,
        }
    except Exception as e:
        return {"message": "Link Scraper Workflow failed", "error": str(e)}


@router.post("/content")
def scrape_content():
    task = content_scraper.delay()
    return {"message": "Content scraping started", "task_id": task.id}
