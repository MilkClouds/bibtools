"""Data models for bibtex verification and generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum

# =============================================================================
# Paper Metadata Models
# =============================================================================


@dataclass
class PaperMetadata:
    """Unified paper metadata from CrossRef or arXiv."""

    title: str
    authors: list[dict[str, str]]  # [{'given': 'John', 'family': 'Doe'}, ...]
    year: int | None
    venue: str | None
    doi: str | None = None
    arxiv_id: str | None = None
    source: str = ""  # "crossref" or "arxiv"


@dataclass
class SourceDiscrepancy:
    """Discrepancy between data sources (e.g., CrossRef vs Semantic Scholar)."""

    field: str
    primary_value: str
    secondary_value: str


@dataclass
class FetchResult:
    """Result of fetching paper metadata and generating bibtex."""

    bibtex: str
    metadata: PaperMetadata
    discrepancies: list[SourceDiscrepancy] = field(default_factory=list)


class VerificationStatus(IntEnum):
    """Verification status for an entry or overall report.

    Uses IntEnum so min(statuses) gives the worst status.
    PASS=0, WARNING=1, FAIL=2 -> min gives worst case.
    """

    PASS = 0
    WARNING = 1
    FAIL = 2


@dataclass
class BibtexEntry:
    """Bibtex entry with essential fields only.

    Handles parsing from raw bibtex and serialization to normalized format.
    All parsing logic is encapsulated here.
    """

    key: str
    title: str
    authors: list[str]
    venue: str | None
    year: int | None
    entry_type: str = "inproceedings"  # "article" or "inproceedings"

    @classmethod
    def from_raw_bibtex(cls, raw_bibtex: str) -> BibtexEntry | None:
        """Parse raw bibtex string into BibtexEntry.

        Args:
            raw_bibtex: Raw bibtex string from Semantic Scholar.

        Returns:
            BibtexEntry or None if parsing fails.
        """
        if not raw_bibtex:
            return None

        # Extract entry type and key
        entry_match = re.match(r"@(\w+)\s*\{\s*([^,]+),", raw_bibtex, re.IGNORECASE)
        if not entry_match:
            return None

        entry_type_raw = entry_match.group(1).lower()
        key = entry_match.group(2).strip()

        # Normalize entry type
        entry_type = "article" if entry_type_raw == "article" else "inproceedings"

        # Extract fields (use word boundary to avoid "title" matching "booktitle")
        def extract_field(name: str) -> str | None:
            pattern = rf"(?:^|[,\s]){name}\s*=\s*[\{{\"](.*?)[\}}\"]"
            match = re.search(pattern, raw_bibtex, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            return match.group(1).strip() if match else None

        title = extract_field("title") or ""

        # Require title to be present for a valid entry
        if not title:
            return None

        # Parse authors
        author_str = extract_field("author")
        authors = []
        if author_str:
            authors = [a.strip() for a in author_str.split(" and ") if a.strip()]

        # Venue: booktitle (conference) or journal (article)
        venue = extract_field("booktitle") or extract_field("journal")

        # Year
        year_str = extract_field("year")
        year = int(year_str) if year_str and year_str.isdigit() else None

        return cls(
            key=key,
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            entry_type=entry_type,
        )

    def to_bibtex(self, paper_id: str | None = None) -> str:
        """Serialize to normalized bibtex string.

        Output format: title, author, booktitle/journal, year (in that order).
        Only these 4 fields are included.

        Args:
            paper_id: Optional paper_id to include as comment.

        Returns:
            Normalized bibtex string.
        """
        fields = []
        if self.title:
            fields.append(f"  title = {{{self.title}}}")
        if self.authors:
            fields.append(f"  author = {{{' and '.join(self.authors)}}}")
        if self.venue:
            venue_field = "journal" if self.entry_type == "article" else "booktitle"
            fields.append(f"  {venue_field} = {{{self.venue}}}")
        if self.year is not None:
            fields.append(f"  year = {{{self.year}}}")

        fields_str = ",\n".join(fields)
        bibtex = f"@{self.entry_type}{{{self.key},\n{fields_str}\n}}"

        if paper_id:
            return f"% paper_id: {paper_id}\n{bibtex}"
        return bibtex

    def get_venue_short(self) -> str | None:
        """Get a short venue name for the verification comment."""
        if not self.venue:
            return None

        from .venue_aliases import get_venue_short as _get_venue_short

        return _get_venue_short(self.venue)


@dataclass
class PaperInfo:
    """Paper information from Semantic Scholar.

    Contains only paper_id and bibtex entry.
    All other fields are accessed via bibtex property.
    """

    paper_id: str
    bibtex: BibtexEntry

    @property
    def title(self) -> str:
        """Get title from bibtex."""
        return self.bibtex.title

    @property
    def authors(self) -> list[str]:
        """Get authors from bibtex."""
        return self.bibtex.authors

    @property
    def venue(self) -> str | None:
        """Get venue from bibtex."""
        return self.bibtex.venue

    @property
    def year(self) -> int | None:
        """Get year from bibtex."""
        return self.bibtex.year

    def get_venue_short(self) -> str | None:
        """Get a short venue name for the verification comment."""
        return self.bibtex.get_venue_short()


@dataclass
class FieldMismatch:
    """Information about a field mismatch between bibtex and fetched source."""

    field_name: str
    bibtex_value: str
    fetched_value: str  # From CrossRef/arXiv/S2
    source: str = ""  # "crossref", "arxiv", or "S2"
    similarity: float | None = None  # For title comparison
    is_warning: bool = False  # True if only differs by LaTeX braces (not a hard error)


@dataclass
class VerificationResult:
    """Result of verifying a single bibtex entry."""

    entry_key: str
    success: bool
    message: str
    paper_info: PaperInfo | None = None
    already_verified: bool = False
    needs_update: bool = False
    no_paper_id: bool = False  # Entry has no paper_id (warning)
    paper_id_used: str | None = None  # The paper_id used for lookup
    auto_found_paper_id: bool = False  # True if paper_id was auto-found (not from comment)
    paper_id_source: str | None = None  # Source of paper_id: "comment", "doi", "eprint"
    mismatches: list[FieldMismatch] = field(default_factory=list)  # Hard errors (FAIL)
    warnings: list[FieldMismatch] = field(default_factory=list)  # Soft warnings (WARNING)
    fixed: bool = False  # True if fields were auto-fixed

    @property
    def status(self) -> VerificationStatus:
        """Get verification status for this entry.

        - FAIL: Has mismatches (not fixed) or lookup failed
        - WARNING: Passed but has warnings (e.g., title case difference)
        - PASS: All checks passed with no warnings
        """
        if self.mismatches and not self.fixed:
            return VerificationStatus.FAIL
        if not self.success and not self.already_verified and not self.no_paper_id:
            return VerificationStatus.FAIL
        if self.warnings:
            return VerificationStatus.WARNING
        if self.no_paper_id:
            return VerificationStatus.WARNING
        return VerificationStatus.PASS


@dataclass
class VerificationReport:
    """Overall verification report."""

    total_entries: int = 0
    verified: int = 0
    verified_with_warnings: int = 0  # Verified but with warnings
    already_verified: int = 0
    failed: int = 0
    no_paper_id: int = 0  # Entries without paper_id (warnings)
    fixed: int = 0  # Entries with auto-fixed fields
    results: list[VerificationResult] = field(default_factory=list)

    def add_result(self, result: VerificationResult) -> None:
        """Add a verification result to the report."""
        self.results.append(result)
        self.total_entries += 1
        if result.already_verified:
            self.already_verified += 1
        elif result.no_paper_id:
            self.no_paper_id += 1
        elif result.fixed:
            self.fixed += 1
        elif result.success:
            if result.warnings:
                self.verified_with_warnings += 1
            else:
                self.verified += 1
        else:
            self.failed += 1

    @property
    def overall_status(self) -> VerificationStatus:
        """Get overall verification status.

        Returns worst status among all entries:
        - FAIL if any entry failed
        - WARNING if any entry has warnings (including no_paper_id)
        - PASS if all entries passed without warnings
        """
        if self.failed > 0:
            return VerificationStatus.FAIL
        if self.verified_with_warnings > 0 or self.no_paper_id > 0:
            return VerificationStatus.WARNING
        return VerificationStatus.PASS

    @property
    def exit_code(self) -> int:
        """Get CLI exit code based on overall status.

        - 0: PASS (all entries verified without issues)
        - 1: WARNING (some entries have warnings)
        - 2: FAIL (some entries failed verification)
        """
        return int(self.overall_status)
