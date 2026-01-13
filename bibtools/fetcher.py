"""Metadata fetcher with single source of truth principle."""

import os

from . import logging as logger
from .arxiv_client import ArxivClient
from .crossref import CrossRefClient
from .dblp import DBLPClient
from .models import PaperMetadata
from .semantic_scholar import ResolvedIds, SemanticScholarClient


class MetadataFetcher:
    """Fetches paper metadata from CrossRef/DBLP/arXiv via S2 resolution."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        s2_client: SemanticScholarClient | None = None,
        crossref_client: CrossRefClient | None = None,
        dblp_client: DBLPClient | None = None,
        arxiv_client: ArxivClient | None = None,
    ):
        effective_api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.s2_client = s2_client or SemanticScholarClient(api_key=effective_api_key)
        self.crossref_client = crossref_client or CrossRefClient()
        self.dblp_client = dblp_client or DBLPClient()
        self.arxiv_client = arxiv_client or ArxivClient()
        self._owns_s2 = s2_client is None
        self._owns_crossref = crossref_client is None
        self._owns_dblp = dblp_client is None

    def close(self) -> None:
        """Close owned clients."""
        if self._owns_s2:
            self.s2_client.close()
        if self._owns_crossref:
            self.crossref_client.close()
        if self._owns_dblp:
            self.dblp_client.close()

    def __enter__(self) -> "MetadataFetcher":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def fetch(self, paper_id: str) -> PaperMetadata | None:
        """Fetch paper metadata by paper_id.

        Flow:
        1. S2 resolves paper_id → DOI/arXiv ID + venue
        2. Source selection (mutually exclusive):
           - if DOI exists        → CrossRef
           - elif venue != arXiv  → DBLP
           - elif venue == arXiv  → arXiv
           - else                 → FAIL (return None)
        """
        resolved = self.s2_client.resolve_ids(paper_id)
        if not resolved:
            logger.debug(f"Paper not found in Semantic Scholar: {paper_id}")
            return None

        logger.info(f"Resolved: {paper_id} | DOI={resolved.doi} | arXiv={resolved.arxiv_id} | venue={resolved.venue}")
        return self._fetch_with_resolved(resolved)

    def _fetch_with_resolved(self, resolved: ResolvedIds) -> PaperMetadata | None:
        """Fetch metadata using resolved IDs."""
        # Case 1: DOI exists -> CrossRef
        if resolved.doi:
            logger.info("Source: crossref (DOI exists)")
            meta = self.crossref_client.get_paper_metadata(resolved.doi)
            if meta:
                return PaperMetadata(
                    title=meta.title,
                    authors=meta.authors,
                    year=meta.year,
                    venue=meta.venue,
                    doi=meta.doi,
                    arxiv_id=resolved.arxiv_id,
                    source="crossref",
                )
            return None

        # Case 2: No DOI, venue != arXiv -> DBLP
        if not self._is_arxiv_venue(resolved.venue):
            logger.info(f"Source: dblp (venue={resolved.venue})")
            if resolved.title:
                meta = self.dblp_client.search_by_title(resolved.title, resolved.venue)
                if meta:
                    return PaperMetadata(
                        title=meta.title,
                        authors=meta.authors,
                        year=meta.year,
                        venue=meta.venue,
                        doi=meta.doi,
                        arxiv_id=resolved.arxiv_id,
                        source="dblp",
                    )
            return None

        # Case 3: No DOI, venue == arXiv -> arXiv
        if resolved.arxiv_id:
            logger.info("Source: arxiv")
            meta = self.arxiv_client.get_paper_metadata(resolved.arxiv_id)
            if meta:
                return PaperMetadata(
                    title=meta.title,
                    authors=meta.authors,
                    year=meta.year,
                    venue=meta.venue,
                    arxiv_id=meta.arxiv_id,
                    source="arxiv",
                )

        return None

    def _is_arxiv_venue(self, venue: str | None) -> bool:
        """Check if venue indicates arXiv preprint."""
        if not venue:
            return True
        venue_lower = venue.lower()
        return "arxiv" in venue_lower or venue_lower in ("", "corr")

