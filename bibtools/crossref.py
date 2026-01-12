"""CrossRef API client for paper metadata."""

import time
from dataclasses import dataclass

import httpx

from .models import Author
from .rate_limiter import RateLimiter


@dataclass
class CrossRefMetadata:
    """Paper metadata from CrossRef."""

    title: str
    authors: list[Author]
    venue: str | None
    year: int | None
    doi: str


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
        self._rate_limiter = RateLimiter(min_interval=0.02)
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

    def get_authors_by_doi(self, doi: str) -> list[Author] | None:
        """Get author names by DOI. Returns None if not found."""
        meta = self.get_paper_metadata(doi)
        return meta.authors if meta and meta.authors else None

    def get_paper_metadata(self, doi: str) -> CrossRefMetadata | None:
        """Get full paper metadata by DOI. Raises CrossRefError on API failure."""
        doi = doi[4:] if doi.upper().startswith("DOI:") else doi
        message = self._fetch_work(doi)
        return self._parse_metadata(message, doi) if message else None

    def _fetch_work(self, doi: str) -> dict | None:
        """Fetch work data from CrossRef API. Returns None if 404."""
        client = self._get_http_client()
        request_url = f"{self.BASE_URL}/works/{doi}"

        for attempt in range(self.max_retries):
            try:
                response = self._rate_limiter.execute(lambda url=request_url: client.get(url))

                if response.status_code == 404:
                    return None
                if response.status_code == 429:
                    time.sleep((attempt + 1) * 5)
                    continue

                response.raise_for_status()
                return response.json().get("message", {})

            except httpx.HTTPError as e:
                if attempt < self.max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue
                raise CrossRefError(f"Failed to fetch DOI {doi}: {e}") from e

        raise CrossRefError(f"Failed to fetch DOI {doi} after {self.max_retries} retries")

    def _parse_metadata(self, message: dict, doi: str) -> CrossRefMetadata:
        """Parse CrossRef API response into CrossRefMetadata."""
        # Title
        titles = message.get("title", [])
        title = titles[0] if titles else ""

        # Authors
        authors: list[Author] = []
        for author in message.get("author", []):
            if "family" in author:
                authors.append(Author(given=author.get("given", ""), family=author["family"]))

        # Venue: container-title (journal/proceedings name)
        containers = message.get("container-title", [])
        venue = containers[0] if containers else None

        # Year: from published or issued date
        year = None
        for date_field in ["published", "issued"]:
            date_parts = message.get(date_field, {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
                break

        return CrossRefMetadata(title=title, authors=authors, venue=venue, year=year, doi=doi)


class CrossRefError(Exception):
    """Error from CrossRef API."""

    pass
