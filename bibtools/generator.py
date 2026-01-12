"""Bibtex generation from Semantic Scholar data."""

import os

from .models import PaperInfo
from .semantic_scholar import SemanticScholarClient


class BibtexGenerator:
    """Generate bibtex entries from Semantic Scholar."""

    def __init__(self, api_key: str | None = None):
        """Initialize the generator.

        Args:
            api_key: Optional Semantic Scholar API key. Falls back to SEMANTIC_SCHOLAR_API_KEY env var.
        """
        effective_api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.client = SemanticScholarClient(api_key=effective_api_key)

    def fetch_by_paper_id(self, paper_id: str) -> tuple[str | None, PaperInfo | None]:
        """Fetch bibtex by paper_id.

        Args:
            paper_id: Paper ID (ARXIV:id, DOI:doi, etc.)

        Returns:
            Tuple of (bibtex_string, paper_info) or (None, None) if not found.
        """
        paper = self.client.get_paper(paper_id)
        if not paper:
            return None, None

        bibtex = paper.bibtex.to_bibtex(paper_id)
        return bibtex, paper

    def search_by_query(self, query: str, limit: int = 5) -> list[tuple[str, PaperInfo]]:
        """Search papers by query and return bibtex entries.

        Args:
            query: Search query (title, keywords).
            limit: Maximum number of results.

        Returns:
            List of (bibtex_string, paper_info) tuples.
            Papers with abbreviated authors are excluded.
        """
        papers = self.client.search_by_title(query, limit=limit)
        results = []
        for paper in papers:
            # Use Semantic Scholar paper_id as identifier
            bibtex = paper.bibtex.to_bibtex(paper.paper_id)
            results.append((bibtex, paper))
        return results
