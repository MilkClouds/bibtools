"""DBLP client for paper metadata.

DBLP is used as a source of truth for papers without DOI (e.g., ICLR, some NeurIPS).
"""

import re
from dataclasses import dataclass

import httpx

from . import logging as log
from .models import Author
from .venue_aliases import get_canonical_venue


@dataclass
class DBLPMetadata:
    """Paper metadata from DBLP."""

    title: str
    authors: list[Author]
    year: int
    venue: str
    dblp_key: str
    doi: str | None = None


class DBLPClient:
    """Client for DBLP API.

    Fetches paper metadata by DBLP key (e.g., "conf/iclr/HuSWALWWC22").
    """

    BASE_URL = "https://dblp.org"

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "DBLPClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def get_paper_metadata(self, dblp_key: str) -> DBLPMetadata | None:
        """Get paper metadata by DBLP key.

        Args:
            dblp_key: DBLP key like "conf/iclr/HuSWALWWC22"

        Returns:
            DBLPMetadata if found, None otherwise.
        """
        try:
            # Build search query from DBLP key
            # Format: conf/iclr/HuSWALWWC22 or journals/corr/abs-2106-09685
            query = self._build_search_query(dblp_key)

            resp = self._client.get(
                f"{self.BASE_URL}/search/publ/api",
                params={"q": query, "format": "json", "h": 10},
            )
            resp.raise_for_status()
            data = resp.json()

            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if not hits:
                return None

            # Find exact match by key
            for hit in hits:
                info = hit.get("info", {})
                if info.get("key") == dblp_key:
                    return self._parse_info(info, dblp_key)

            return None

        except httpx.HTTPError:
            log.debug(f"DBLP HTTP error for key: {dblp_key}")
            return None

    def search_by_title(self, title: str, venue: str | None = None) -> DBLPMetadata | None:
        """Search for a paper by title (and optionally venue).

        This is used when DBLP ID from Semantic Scholar is an arXiv key
        (journals/corr/...) but the paper was actually published at a conference.

        Args:
            title: Paper title to search for
            venue: Optional venue name (e.g., "NeurIPS", "ICLR") to filter results

        Returns:
            DBLPMetadata if found, None otherwise.
        """
        if not title:
            return None

        try:
            # Build search query: title + canonical venue (for DBLP search)
            query = title
            if venue:
                # Use canonical short name for better DBLP search
                # e.g., "Neural Information Processing Systems" -> "NIPS"
                canonical = get_canonical_venue(venue)
                # DBLP uses NIPS for older NeurIPS
                search_venue = canonical if canonical else venue
                if search_venue.upper() == "NEURIPS":
                    search_venue = "NIPS"  # DBLP uses NIPS
                query = f"{title} {search_venue}"

            log.debug(f"DBLP title search: {query[:80]}...")

            resp = self._client.get(
                f"{self.BASE_URL}/search/publ/api",
                params={"q": query, "format": "json", "h": 10},
            )
            resp.raise_for_status()
            data = resp.json()

            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if not hits:
                log.debug("DBLP title search: no results")
                return None

            # Find best match - prefer conference papers over arXiv
            for hit in hits:
                info = hit.get("info", {})
                hit_key = info.get("key", "")

                # Skip arXiv entries (journals/corr/...)
                if hit_key.startswith("journals/corr"):
                    continue

                # Check title similarity (case-insensitive)
                hit_title = (info.get("title") or "").rstrip(".")
                if self._titles_match(title, hit_title):
                    log.debug(f"DBLP title search: found {hit_key}")
                    return self._parse_info(info, hit_key)

            log.debug("DBLP title search: no matching conference paper")
            return None

        except httpx.HTTPError:
            log.debug(f"DBLP HTTP error for title search: {title[:50]}")
            return None

    def _titles_match(self, title1: str, title2: str) -> bool:
        """Check if two titles match (case-insensitive, ignore punctuation)."""

        def normalize(t: str) -> str:
            # Remove punctuation and extra whitespace, lowercase
            t = re.sub(r"[^\w\s]", " ", t.lower())
            return " ".join(t.split())

        return normalize(title1) == normalize(title2)

    def _build_search_query(self, dblp_key: str) -> str:
        """Build a search query from DBLP key.

        Examples:
            conf/iclr/HuSWALWWC22 -> "Hu ICLR 2022" (first author + venue + year)
            journals/corr/abs-2106-09685 -> returns key as-is
        """
        parts = dblp_key.split("/")
        if len(parts) < 3:
            return dblp_key

        key_type = parts[0]  # conf, journals
        venue = parts[1]  # iclr, corr, etc.
        suffix = parts[-1]  # HuSWALWWC22, abs-2106-09685

        # Extract year and first author from suffix
        # Pattern: AuthorName + AuthorInitials + YearSuffix (e.g., HuSWALWWC22)
        year_match = re.search(r"(\d{2})$", suffix)
        if year_match and key_type == "conf":
            year_suffix = year_match.group(1)
            year = f"20{year_suffix}" if int(year_suffix) < 50 else f"19{year_suffix}"

            # Extract first author name (before the initials)
            # HuSWALWWC22 -> Hu (first uppercase word)
            author_match = re.match(r"([A-Z][a-z]+|[0-9]+)", suffix)
            first_author = author_match.group(1) if author_match else ""

            if first_author:
                return f"{first_author} {venue.upper()} {year}"
            return f"{venue.upper()} {year}"

        return dblp_key

    def _parse_info(self, info: dict, dblp_key: str) -> DBLPMetadata | None:
        """Parse DBLP API response info into DBLPMetadata."""
        title = info.get("title", "")
        if not title:
            return None

        # Remove trailing period from title
        title = title.rstrip(".")

        # Parse year
        year_str = info.get("year", "")
        try:
            year = int(year_str)
        except (ValueError, TypeError):
            return None

        # Parse venue
        venue = info.get("venue", "")

        # Parse authors
        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        authors = [self._parse_author(a) for a in authors_data]
        authors = [a for a in authors if a]

        # Get DOI if available
        doi = info.get("doi")

        return DBLPMetadata(
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            dblp_key=dblp_key,
            doi=doi,
        )

    def _parse_author(self, author_data: dict | str) -> Author | None:
        """Parse author data into Author dict."""
        if isinstance(author_data, str):
            name = author_data
        else:
            name = author_data.get("text", "")

        if not name:
            return None

        # Remove numeric suffix (e.g., "Yang Yu 0001" -> "Yang Yu")
        name = re.sub(r"\s+\d{4}$", "", name)

        # Split into given/family
        parts = name.rsplit(None, 1)
        if len(parts) == 2:
            return Author(given=parts[0], family=parts[1])
        return Author(given="", family=parts[0]) if parts else None


class DBLPError(Exception):
    """Error from DBLP API."""

    pass
