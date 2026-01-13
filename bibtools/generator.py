"""Bibtex generation with single source of truth principle."""

from .fetcher import MetadataFetcher
from .models import BibtexEntry, FetchResult, PaperInfo, PaperMetadata
from .utils import format_author_bibtex_style


class BibtexGenerator:
    """Generate bibtex entries with single source of truth."""

    def __init__(self, api_key: str | None = None, *, fetcher: MetadataFetcher | None = None):
        """Initialize the generator.

        Args:
            api_key: Optional Semantic Scholar API key.
            fetcher: Optional pre-configured MetadataFetcher (for sharing).
        """
        self._fetcher = fetcher or MetadataFetcher(api_key=api_key)
        self._owns_fetcher = fetcher is None

    def close(self) -> None:
        """Close owned fetcher."""
        if self._owns_fetcher:
            self._fetcher.close()

    def __enter__(self) -> "BibtexGenerator":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def fetch_by_paper_id(self, paper_id: str) -> FetchResult | None:
        """Fetch bibtex by paper_id. See MetadataFetcher.fetch for flow documentation."""
        metadata = self._fetcher.fetch(paper_id)
        if not metadata:
            return None

        bibtex = self._metadata_to_bibtex(metadata, paper_id)
        return FetchResult(bibtex=bibtex, metadata=metadata)

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
        paper = self._fetcher.s2_client.get_paper(paper_id)
        if not paper:
            return None, None
        bibtex = paper.bibtex.to_bibtex(paper_id)
        return bibtex, paper

    def search_by_query(self, query: str, limit: int = 5) -> list[tuple[str, PaperInfo]]:
        """Search papers by query (uses legacy SS-based flow)."""
        papers = self._fetcher.s2_client.search_by_title(query, limit=limit)
        results = []
        for paper in papers:
            bibtex = paper.bibtex.to_bibtex(paper.paper_id)
            results.append((bibtex, paper))
        return results
