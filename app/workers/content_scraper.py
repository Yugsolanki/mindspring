import asyncio
from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, retry_backoff=30)
def content_scraper(self, *args, **kwargs):
    result = asyncio.run(run(kwargs.get("a"), kwargs.get("b")))
    return result


async def run(a: int, b: int) -> int:
    await asyncio.sleep(10)
    return a + b
