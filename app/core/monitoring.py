from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Callable
from fastapi import Request, Response
import time

# Application Info
app_info = Info("mindspring_app", "MindSpring Application Info")
app_info.info(
    {
        "app_name": "MindSpring API",
        "version": "1.0.0",
        "description": "MindSpring API",
        "service": "mindspring_api",
    }
)

# Request Metrics
http_requests_total = Counter(
    "mindspring_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)


http_request_duration_seconds = Histogram(
    "mindspring_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "mindspring_http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Scraping metrics
scraping_jobs_total = Counter(
    "mindspring_scraping_jobs_total", "Total scraping jobs", ["status", "job_type"]
)

scraping_duration_seconds = Histogram(
    "mindspring_scraping_duration_seconds",
    "Scraping job duration in seconds",
    ["job_type"],
)

active_scraping_jobs = Gauge(
    "mindspring_active_scraping_jobs", "Currently active scraping jobs"
)

# Database metrics
db_connections_active = Gauge(
    "mindspring_db_connections_active", "Active database connections"
)

db_query_duration_seconds = Histogram(
    "mindspring_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)

# Celery metrics
celery_tasks_total = Counter(
    "mindspring_celery_tasks_total", "Total Celery tasks", ["task_name", "status"]
)

celery_task_duration_seconds = Histogram(
    "mindspring_celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
)

celery_queue_length = Gauge(
    "mindspring_celery_queue_length", "Number of tasks in Celery queue", ["queue_name"]
)


def create_metrics_middleware() -> Callable:
    """Create middleware for tracking HTTP metrics."""

    async def metrics_middleware(request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Track request duration
        start_time = time.time()

        try:
            response: Response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            http_requests_total.labels(
                method=method, endpoint=endpoint, status=response.status_code
            ).inc()

            return response

        finally:
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    return metrics_middleware
