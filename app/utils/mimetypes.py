from typing import Literal, Optional
from urllib.parse import urlparse
import os

AllowedFileTypes = Literal[
    "text/html",
    "text/plain",
    "application/json",
    "application/xml",
    "application/xhtml+xml",
    "application/rss+xml",
    "application/atom+xml",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

AllowedContentTypes = Literal[
    "text/plain",
    "application/json",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

_EXTENSION_TO_FILE_TYPE: dict[str, AllowedFileTypes] = {
    ".html": "text/html",
    ".htm": "text/html",
    ".txt": "text/plain",
    ".json": "application/json",
    ".xml": "application/xml",
    ".xhtml": "application/xhtml+xml",
    ".rss": "application/rss+xml",
    ".atom": "application/atom+xml",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpg",
    ".webp": "image/webp",
}

_ALLOWED_CONTENT_TYPES: set[AllowedContentTypes] = {
    "text/plain",
    "application/json",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}


def infer_file_type_from_url(url: str) -> Optional[AllowedFileTypes]:
    """
    Infer file type from url

    Args:
        url (str): url to infer file type from

    Returns:
        Optional[AllowedFileTypes]: file type if found, "text/html" otherwise
    """
    parsed = urlparse(url)
    path = parsed.path.lower()

    _, ext = os.path.splitext(path)

    if not ext:
        return "text/html"

    return _EXTENSION_TO_FILE_TYPE.get(ext)


def is_allowed_content_type(url: str) -> bool:
    """
    Check if the url is allowed content type

    Args:
        url (str): url to check

    Returns:
        bool: True if the url is allowed content type, False otherwise
    """
    file_type = infer_file_type_from_url(url)
    if file_type is None:
        return False
    return file_type in _ALLOWED_CONTENT_TYPES
