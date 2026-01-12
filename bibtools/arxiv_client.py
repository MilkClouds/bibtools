"""arXiv API client for paper metadata."""

from dataclasses import dataclass

import arxiv

from .models import Author


@dataclass
class ArxivMetadata:
    """Paper metadata from arXiv."""

    title: str
    authors: list[Author]
    year: int
    arxiv_id: str
    venue: str = "arXiv"


class ArxivClient:
    """Client for arXiv API."""

    def __init__(self) -> None:
        self._client = arxiv.Client()

    def get_authors_by_arxiv_id(self, arxiv_id: str) -> list[Author] | None:
        """Get author names by arXiv ID. Returns None if not found."""
        result = self._fetch_paper(arxiv_id)
        return result.authors if result else None

    def get_paper_metadata(self, arxiv_id: str) -> ArxivMetadata | None:
        """Get full paper metadata by arXiv ID."""
        return self._fetch_paper(arxiv_id)

    def _fetch_paper(self, arxiv_id: str) -> ArxivMetadata | None:
        """Fetch paper from arXiv API.

        Returns:
            ArxivMetadata if found, None if not found.

        Raises:
            ArxivError: On network or API errors.
        """
        normalized_id = self._normalize_arxiv_id(arxiv_id)
        try:
            search = arxiv.Search(id_list=[normalized_id])
            results = list(self._client.results(search))
            if not results:
                return None

            paper = results[0]
            authors = [self._parse_author_name(a.name) for a in paper.authors]
            authors = [a for a in authors if a]

            return ArxivMetadata(
                title=paper.title,
                authors=authors,
                year=paper.published.year,
                arxiv_id=normalized_id,
            )
        except arxiv.HTTPError as e:
            raise ArxivError(f"HTTP error fetching {arxiv_id}: {e}") from e
        except arxiv.UnexpectedEmptyPageError as e:
            # Paper not found (empty response)
            return None
        except Exception as e:
            raise ArxivError(f"Error fetching {arxiv_id}: {e}") from e

    def _normalize_arxiv_id(self, arxiv_id: str) -> str:
        """Normalize arXiv ID: remove prefix and version suffix."""
        arxiv_id = arxiv_id.upper().removeprefix("ARXIV:").lower()
        if "v" in arxiv_id:
            arxiv_id = arxiv_id.rsplit("v", 1)[0]
        return arxiv_id

    def _parse_author_name(self, name: str) -> Author | None:
        """Parse 'Firstname Lastname' into Author dict."""
        name = " ".join(name.split())
        if not name:
            return None
        parts = name.rsplit(None, 1)
        if len(parts) == 2:
            return Author(given=parts[0], family=parts[1])
        return Author(given="", family=parts[0]) if parts else None


class ArxivError(Exception):
    """Error from arXiv API."""

    pass
