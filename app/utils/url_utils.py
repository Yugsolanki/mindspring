def normalize_url(url: str) -> str:
    """Normalize URL for consistent matching across the scraping pipeline.

    - Converts to lowercase
    - Strips trailing slashes
    - Removes fragments

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL string
    """
    url = url.lower()
    url = url.rstrip("/")
    url = url.split("#")[0]
    return url
