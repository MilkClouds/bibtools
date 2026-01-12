"""Bibtex generation using CrossRef (primary) and arXiv (fallback).

Architecture:
1. Semantic Scholar: Resolve identifier → DOI/arXiv ID
2. CrossRef: Fetch metadata if DOI exists (not arXiv DOI)
3. arXiv: Fetch metadata if no DOI or arXiv-only
"""

import os

from .arxiv_client import ArxivClient, ArxivMetadata
from .crossref import CrossRefClient, CrossRefError, CrossRefMetadata
from .models import BibtexEntry, FetchResult, PaperInfo, PaperMetadata, SourceDiscrepancy
from .semantic_scholar import ResolvedIds, SemanticScholarClient
from .utils import format_author_bibtex_style


class BibtexGenerator:
    """Generate bibtex entries. Primary: CrossRef, Fallback: arXiv."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        ss_client: SemanticScholarClient | None = None,
        crossref_client: CrossRefClient | None = None,
        arxiv_client: ArxivClient | None = None,
    ):
        """Initialize the generator.

        Args:
            api_key: Optional Semantic Scholar API key.
            ss_client: Optional pre-configured SemanticScholarClient (for sharing).
            crossref_client: Optional pre-configured CrossRefClient (for sharing).
            arxiv_client: Optional pre-configured ArxivClient (for sharing).
        """
        effective_api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.ss_client = ss_client or SemanticScholarClient(api_key=effective_api_key)
        self.crossref_client = crossref_client or CrossRefClient()
        self.arxiv_client = arxiv_client or ArxivClient()
        # Track which clients we own (for proper cleanup)
        self._owns_ss = ss_client is None
        self._owns_crossref = crossref_client is None
        self._owns_arxiv = arxiv_client is None

    def close(self) -> None:
        """Close owned clients only."""
        if self._owns_ss:
            self.ss_client.close()
        if self._owns_crossref:
            self.crossref_client.close()
        # ArxivClient doesn't need closing (uses feedparser, no persistent connection)

    def __enter__(self) -> "BibtexGenerator":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def fetch_by_paper_id(self, paper_id: str) -> FetchResult | None:
        """Fetch bibtex by paper_id using new architecture.

        Flow: SS resolve → CrossRef (if DOI) → arXiv (fallback)
        Returns None if paper not found. Raises on API errors.
        """
        # Step 1: Resolve identifier via Semantic Scholar
        resolved = self.ss_client.resolve_ids(paper_id)
        if not resolved:
            return None

        return self._fetch_with_resolved_ids(paper_id, resolved)

    def _fetch_with_resolved_ids(self, paper_id: str, resolved: ResolvedIds) -> FetchResult | None:
        """Fetch metadata using resolved DOI/arXiv ID."""
        discrepancies: list[SourceDiscrepancy] = []

        # Step 2: Try CrossRef if DOI exists
        if resolved.doi:
            crossref_meta = self.crossref_client.get_paper_metadata(resolved.doi)
            if crossref_meta:
                metadata = self._crossref_to_metadata(crossref_meta)
                bibtex = self._metadata_to_bibtex(metadata, paper_id)
                return FetchResult(bibtex=bibtex, metadata=metadata, discrepancies=discrepancies)
            # CrossRef failed with DOI - this is an error
            raise CrossRefError(f"DOI exists but CrossRef lookup failed: {resolved.doi}")

        # Step 3: arXiv fallback (venue is always "arXiv" - source of truth principle)
        if resolved.arxiv_id:
            arxiv_meta = self.arxiv_client.get_paper_metadata(resolved.arxiv_id)
            if arxiv_meta:
                metadata = self._arxiv_to_metadata(arxiv_meta)
                bibtex = self._metadata_to_bibtex(metadata, paper_id)
                return FetchResult(bibtex=bibtex, metadata=metadata, discrepancies=discrepancies)

        return None

    def _crossref_to_metadata(self, cr: CrossRefMetadata) -> PaperMetadata:
        """Convert CrossRefMetadata to unified PaperMetadata."""
        return PaperMetadata(
            title=cr.title,
            authors=cr.authors,
            year=cr.year,
            venue=cr.venue,
            doi=cr.doi,
            source="crossref",
        )

    def _arxiv_to_metadata(self, ar: ArxivMetadata) -> PaperMetadata:
        """Convert ArxivMetadata to unified PaperMetadata."""
        return PaperMetadata(
            title=ar.title,
            authors=ar.authors,
            year=ar.year,
            venue=ar.venue,  # Always "arXiv" from ArxivMetadata
            arxiv_id=ar.arxiv_id,
            source="arxiv",
        )

    def _metadata_to_bibtex(self, meta: PaperMetadata, paper_id: str) -> str:
        """Convert PaperMetadata to bibtex string."""
        # Format authors to bibtex style
        authors = [format_author_bibtex_style(a["given"], a["family"]) for a in meta.authors]

        # Determine entry type
        entry_type = "article" if meta.venue and "journal" in meta.venue.lower() else "inproceedings"

        # Generate key from first author and year
        first_family = meta.authors[0]["family"] if meta.authors else "unknown"
        key = f"{first_family.lower()}{meta.year or ''}"

        entry = BibtexEntry(
            key=key,
            title=meta.title,
            authors=authors,
            venue=meta.venue,
            year=meta.year,
            entry_type=entry_type,
        )
        return entry.to_bibtex(paper_id)

    # Legacy methods for backward compatibility
    def fetch_by_paper_id_legacy(self, paper_id: str) -> tuple[str | None, PaperInfo | None]:
        """Legacy method using old SS-based architecture."""
        paper = self.ss_client.get_paper(paper_id)
        if not paper:
            return None, None
        bibtex = paper.bibtex.to_bibtex(paper_id)
        return bibtex, paper

    def search_by_query(self, query: str, limit: int = 5) -> list[tuple[str, PaperInfo]]:
        """Search papers by query (uses legacy SS-based flow)."""
        papers = self.ss_client.search_by_title(query, limit=limit)
        results = []
        for paper in papers:
            bibtex = paper.bibtex.to_bibtex(paper.paper_id)
            results.append((bibtex, paper))
        return results
