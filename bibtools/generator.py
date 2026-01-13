"""Bibtex generation with single source of truth principle.

Architecture:
1. Semantic Scholar: Resolve identifier → DOI/arXiv ID + venue detection
2. Source selection (mutually exclusive branches):
   - if DOI exists        → CrossRef
   - elif venue != arXiv  → DBLP
   - elif venue == arXiv  → arXiv
   - else                 → FAIL

Each bibtex entry uses exactly ONE source of truth - no fallback.
"""

import os

from . import logging as log
from .arxiv_client import ArxivClient, ArxivMetadata
from .crossref import CrossRefClient, CrossRefError, CrossRefMetadata
from .dblp import DBLPClient, DBLPMetadata
from .models import BibtexEntry, FetchResult, PaperInfo, PaperMetadata, SourceDiscrepancy
from .semantic_scholar import ResolvedIds, SemanticScholarClient
from .utils import format_author_bibtex_style


class BibtexGenerator:
    """Generate bibtex entries. Priority: CrossRef > DBLP > arXiv."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        ss_client: SemanticScholarClient | None = None,
        crossref_client: CrossRefClient | None = None,
        dblp_client: DBLPClient | None = None,
        arxiv_client: ArxivClient | None = None,
    ):
        """Initialize the generator.

        Args:
            api_key: Optional Semantic Scholar API key.
            ss_client: Optional pre-configured SemanticScholarClient (for sharing).
            crossref_client: Optional pre-configured CrossRefClient (for sharing).
            dblp_client: Optional pre-configured DBLPClient (for sharing).
            arxiv_client: Optional pre-configured ArxivClient (for sharing).
        """
        effective_api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.ss_client = ss_client or SemanticScholarClient(api_key=effective_api_key)
        self.crossref_client = crossref_client or CrossRefClient()
        self.dblp_client = dblp_client or DBLPClient()
        self.arxiv_client = arxiv_client or ArxivClient()
        # Track which clients we own (for proper cleanup)
        self._owns_ss = ss_client is None
        self._owns_crossref = crossref_client is None
        self._owns_dblp = dblp_client is None
        self._owns_arxiv = arxiv_client is None

    def close(self) -> None:
        """Close owned clients only."""
        if self._owns_ss:
            self.ss_client.close()
        if self._owns_crossref:
            self.crossref_client.close()
        if self._owns_dblp:
            self.dblp_client.close()
        # ArxivClient doesn't need closing (uses feedparser, no persistent connection)

    def __enter__(self) -> "BibtexGenerator":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def fetch_by_paper_id(self, paper_id: str) -> FetchResult | None:
        """Fetch bibtex by paper_id using single source of truth.

        Flow: SS resolve → CrossRef (DOI) → DBLP (venue != arXiv) → arXiv
        Returns None if paper not found. Raises on API errors.
        """
        # Step 1: Resolve identifier via Semantic Scholar
        resolved = self.ss_client.resolve_ids(paper_id)
        if not resolved:
            log.debug(f"Paper not found in Semantic Scholar: {paper_id}")
            return None

        log.info(f"Resolved: {paper_id} | DOI={resolved.doi} | arXiv={resolved.arxiv_id} | venue={resolved.venue}")
        return self._fetch_with_resolved_ids(paper_id, resolved)

    def _fetch_with_resolved_ids(self, paper_id: str, resolved: ResolvedIds) -> FetchResult | None:
        """Fetch metadata using resolved DOI/arXiv ID + venue.

        Source selection (mutually exclusive):
        - if DOI exists       -> CrossRef
        - elif venue != arXiv -> DBLP
        - else                -> arXiv

        Each entry uses exactly ONE source - no mixing or fallback.
        """
        discrepancies: list[SourceDiscrepancy] = []

        # Case 1: DOI exists -> CrossRef
        if resolved.doi:
            log.info("Source: crossref (DOI exists)")
            crossref_meta = self.crossref_client.get_paper_metadata(resolved.doi)
            if crossref_meta:
                metadata = self._crossref_to_metadata(crossref_meta)
                bibtex = self._metadata_to_bibtex(metadata, paper_id)
                return FetchResult(bibtex=bibtex, metadata=metadata, discrepancies=discrepancies)
            raise CrossRefError(f"DOI exists but CrossRef lookup failed: {resolved.doi}")

        # Case 2: No DOI, venue != arXiv -> DBLP
        venue_is_arxiv = self._is_arxiv_venue(resolved.venue)
        if not venue_is_arxiv:
            log.info(f"Source: dblp (venue={resolved.venue})")
            if resolved.title:
                dblp_meta = self.dblp_client.search_by_title(resolved.title, resolved.venue)
                if dblp_meta:
                    metadata = self._dblp_to_metadata(dblp_meta)
                    bibtex = self._metadata_to_bibtex(metadata, paper_id)
                    return FetchResult(bibtex=bibtex, metadata=metadata, discrepancies=discrepancies)
            return None

        # Case 3: No DOI, venue == arXiv -> arXiv
        if resolved.arxiv_id:
            log.info("Source: arxiv")
            arxiv_meta = self.arxiv_client.get_paper_metadata(resolved.arxiv_id)
            if arxiv_meta:
                metadata = self._arxiv_to_metadata(arxiv_meta)
                bibtex = self._metadata_to_bibtex(metadata, paper_id)
                return FetchResult(bibtex=bibtex, metadata=metadata, discrepancies=discrepancies)

        return None

    def _is_arxiv_venue(self, venue: str | None) -> bool:
        """Check if venue indicates arXiv preprint."""
        if not venue:
            return True  # No venue info, assume arXiv
        venue_lower = venue.lower()
        return "arxiv" in venue_lower or venue_lower in ("", "corr")

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

    def _dblp_to_metadata(self, dblp: DBLPMetadata) -> PaperMetadata:
        """Convert DBLPMetadata to unified PaperMetadata."""
        return PaperMetadata(
            title=dblp.title,
            authors=dblp.authors,
            year=dblp.year,
            venue=dblp.venue,
            doi=dblp.doi,
            source="dblp",
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
