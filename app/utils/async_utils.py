import asyncio

_loop = None


def get_event_loop():
    global _loop
    if _loop is None:
        _loop = asyncio.get_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def run_async(func):
    loop = get_event_loop()
    return loop.run_until_complete(func)
