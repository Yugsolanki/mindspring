from temporalio.client import Client
from app.core.config import settings
from typing import Optional
import asyncio

_client: Optional[Client] = None
_lock = asyncio.Lock()


async def get_temporal_client() -> Client:
    """Get or create a Temporal client singleton"""
    global _client

    async with _lock:
        if _client is None:
            _client = await Client.connect(
                target_host=settings.TEMPORAL_HOST,
                namespace=settings.TEMPORAL_NAMESPACE,
            )
    return _client


async def close_temporal_client() -> None:
    """Close the Temporal client connection"""
    global _client
    async with _lock:
        if _client is not None:
            _client = None
