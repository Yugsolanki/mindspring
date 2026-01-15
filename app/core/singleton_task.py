import threading
from functools import wraps
from app.core.singleton_lock import SingletonLock
import logging

logger = logging.getLogger(__name__)


def singleton_task(lock_name: str, heartbeat_interval: int = 10, stale_after: int = 60):
    """
    Decorator ensuring only one instance of a task runs at a time.
    Uses heartbeat mechanism for long-running tasks with no time limit.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = SingletonLock(lock_name, heartbeat_interval, stale_after)

            if not lock.acquire():
                logger.info(f"Task {lock_name} already running, skipping")
                return {"status": "skipped", "reason": "already running"}

            stop_event = threading.Event()
            heartbeat_failed = threading.Event()

            def heartbeat_loop():
                while not stop_event.wait(heartbeat_interval):
                    if not lock.heartbeat():
                        logger.warning(f"Lost lock ownership for {lock_name}")
                        heartbeat_failed.set()
                        return

            heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
            heartbeat_thread.start()

            try:
                # Optionally check if we lost the lock mid-execution
                result = func(*args, **kwargs)

                if heartbeat_failed.is_set():
                    logger.error(f"Task {lock_name} completed but lock was lost")
                    return {
                        "status": "warning",
                        "reason": "lock lost during execution",
                        "result": result,
                    }

                return result
            finally:
                stop_event.set()
                heartbeat_thread.join(timeout=heartbeat_interval + 1)
                lock.release()

        return wrapper

    return decorator
