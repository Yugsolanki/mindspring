from fastapi import APIRouter
from app.workers.link_scraper import link_scraper
from app.workers.content_scraper import content_scraper

router = APIRouter()


@router.post("/links")
def scrape_links():
    task = link_scraper.delay()
    return {"message": "Link scraping started", "task_id": task.id}


@router.post("/content")
def scrape_content():
    task = content_scraper.delay()
    return {"message": "Content scraping started", "task_id": task.id}
