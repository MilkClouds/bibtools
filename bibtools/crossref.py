"""CrossRef API client for author name resolution."""

import time

import httpx

from .rate_limiter import RateLimiter


class CrossRefClient:
    """Client for CrossRef API to get author full names from DOI."""

    BASE_URL = "https://api.crossref.org"

    def __init__(self, max_retries: int = 3):
        """Initialize the client.

        Args:
            max_retries: Maximum number of retries on errors.
        """
        self.max_retries = max_retries
        # CrossRef allows 50 requests per second for polite users
        # Use 0.1 second interval for polite rate limiting
        self._rate_limiter = RateLimiter(min_interval=0.1)
        self._http_client: httpx.Client | None = None

    def _get_http_client(self) -> httpx.Client:
        """Get or create HTTP client with connection pooling."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.Client(
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    # Polite user-agent for better rate limits
                    "User-Agent": "bibtools/1.0 (https://github.com/bibtools; mailto:bibtools@example.com)",
                },
            )
        return self._http_client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None and not self._http_client.is_closed:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "CrossRefClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def get_authors_by_doi(self, doi: str) -> list[dict[str, str]] | None:
        """Get author information by DOI.

        Args:
            doi: DOI string (with or without 'DOI:' prefix).

        Returns:
            List of author dicts with 'given' and 'family' keys, or None if not found.
            Example: [{'given': 'Michael I.', 'family': 'Posner'}, ...]
        """
        # Remove DOI: prefix if present
        if doi.upper().startswith("DOI:"):
            doi = doi[4:]

        client = self._get_http_client()
        # Capture doi in closure to avoid late binding issues
        request_url = f"{self.BASE_URL}/works/{doi}"

        for attempt in range(self.max_retries):
            try:
                response = self._rate_limiter.execute(lambda url=request_url: client.get(url))

                if response.status_code == 404:
                    return None

                if response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                message = data.get("message", {})
                authors = message.get("author", [])

                result = []
                for author in authors:
                    if "given" in author and "family" in author:
                        result.append(
                            {
                                "given": author["given"],
                                "family": author["family"],
                            }
                        )
                    elif "name" in author:
                        # Organization or single name - skip or handle
                        continue

                return result if result else None

            except httpx.HTTPError:
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue

        return None
