# app/core/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.logging import logger


class AppException(Exception):
    """Base exception for application-specific errors"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)


class DatabaseException(AppException):
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)


class ScrapingException(AppException):
    """Base exception for scraping errors"""


class ScrapingTimeoutException(ScrapingException):
    def __init__(self, url: str, timeout: int):
        super().__init__(f"Timeout ({timeout}s) scraping {url}", status_code=408)


class ScrapingRateLimitException(ScrapingException):
    def __init__(self, url: str, retry_after: int | None = None):
        msg = f"Rate limited scraping {url}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg, status_code=429)


class ScrapingAuthException(ScrapingException):
    def __init__(self, url: str):
        super().__init__(f"Authentication required for {url}", status_code=403)


async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    logger.error(
        f"AppException: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message, "path": request.url.path},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation error",
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors"""
    logger.exception(
        f"Database error: {str(exc)}",
        extra={"path": request.url.path, "method": request.method},
    )

    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "error",
                "message": "Database integrity constraint violated",
                "path": request.url.path,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Database operation failed",
            "path": request.url.path,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions"""
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "path": request.url.path,
        },
    )
