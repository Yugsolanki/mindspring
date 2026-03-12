from fastapi import APIRouter
from app.core.config import settings
from app.core.temporal_client import get_temporal_client
from app.temporal.workflows.link_scraper_workflow import LinkScraperWorkflow
from app.temporal.workflows.content_scraper_workflow import ContentScraperWorkflow
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy, WorkflowIDConflictPolicy

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
            id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
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
async def scrape_content():
    client: Client = await get_temporal_client()

    # Using a fixed workflow ID to ensure singleton execution
    workflow_id = "content-scraper-workflow-singleton"

    try:
        handle = await client.start_workflow(
            workflow=ContentScraperWorkflow,
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
            id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        )

        return {
            "message": "Content Scraper Workflow started",
            "workflow_id": handle.id,
            "run_id": handle.result_run_id,
        }
    except Exception as e:
        return {"message": "Content Scraper Workflow failed", "error": str(e)}
