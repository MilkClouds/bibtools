"""arXiv API client for author name resolution."""

import arxiv


class ArxivClient:
    """Client for arXiv API to get author full names from arXiv ID."""

    def __init__(self) -> None:
        """Initialize the client."""
        self._client = arxiv.Client()

    def get_authors_by_arxiv_id(self, arxiv_id: str) -> list[dict[str, str]] | None:
        """Get author information by arXiv ID.

        Args:
            arxiv_id: arXiv ID string (with or without 'ARXIV:' prefix).
                      Examples: "2106.15928", "ARXIV:2106.15928", "arXiv:2106.15928v1"

        Returns:
            List of author dicts with 'given' and 'family' keys, or None if not found.
            Example: [{'given': 'John', 'family': 'Smith'}, ...]
        """
        # Normalize arXiv ID: remove prefix and version suffix
        arxiv_id = arxiv_id.upper().removeprefix("ARXIV:")
        arxiv_id = arxiv_id.lower()  # arXiv IDs are case-insensitive
        # Remove version suffix (e.g., "v1", "v2")
        if "v" in arxiv_id:
            arxiv_id = arxiv_id.rsplit("v", 1)[0]

        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self._client.results(search))

            if not results:
                return None

            paper = results[0]
            authors = []

            for author in paper.authors:
                name = author.name.strip()
                parsed = self._parse_author_name(name)
                if parsed:
                    authors.append(parsed)

            return authors if authors else None

        except Exception:
            return None

    def _parse_author_name(self, name: str) -> dict[str, str] | None:
        """Parse a full name into given and family components.

        Handles formats like "John Smith", "John M. Smith", "J. Smith".

        Args:
            name: Full author name.

        Returns:
            Dict with 'given' and 'family' keys, or None if parsing fails.
        """
        name = " ".join(name.split())  # Normalize whitespace
        if not name:
            return None

        # Split on last space to get family name
        parts = name.rsplit(None, 1)
        if len(parts) == 2:
            return {"given": parts[0], "family": parts[1]}
        elif len(parts) == 1:
            # Single name - treat as family name
            return {"given": "", "family": parts[0]}

        return None
