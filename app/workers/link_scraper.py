import time
from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, retry_backoff=30)
def link_scraper(self):
    time.sleep(10)
    return "Link Scraper Task Completed"
