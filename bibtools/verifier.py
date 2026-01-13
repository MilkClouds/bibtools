"""Core verification logic."""

import re
from datetime import datetime
from pathlib import Path

from rich.console import Console

from . import logging as log
from .arxiv_client import ArxivClient
from .constants import AUTO_FIND_ID, AUTO_FIND_NONE, AUTO_FIND_TITLE
from .crossref import CrossRefClient
from .dblp import DBLPClient
from .models import FieldMismatch, PaperMetadata, VerificationReport, VerificationResult
from .parser import (
    extract_paper_id_from_entry,
    generate_verification_comment,
    is_entry_verified,
    parse_bib_file,
)
from .semantic_scholar import SemanticScholarClient
from .utils import (
    compare_authors,
    compare_titles,
    compare_venues,
    title_similarity,
)


class BibVerifier:
    """Verifies bibtex entries against CrossRef/arXiv (via Semantic Scholar ID resolution)."""

    def __init__(
        self,
        api_key: str | None = None,
        skip_verified: bool = True,
        max_age_days: int | None = None,
        auto_find_level: str = "id",
        fix_mismatches: bool = False,
        console: Console | None = None,
        *,
        s2_client: SemanticScholarClient | None = None,
        crossref_client: CrossRefClient | None = None,
        dblp_client: DBLPClient | None = None,
        arxiv_client: ArxivClient | None = None,
    ):
        """Initialize the verifier.

        Args:
            api_key: Optional Semantic Scholar API key. Falls back to SEMANTIC_SCHOLAR_API_KEY env var.
            skip_verified: Skip entries that are already verified.
            max_age_days: Re-verify entries older than this many days. None = never re-verify.
                         0 = always re-verify (equivalent to --reverify).
            auto_find_level: Level of auto-find: "none", "id", or "title".
            fix_mismatches: Automatically fix mismatched fields.
            console: Rich console for output.
            s2_client: Optional pre-configured SemanticScholarClient (for sharing).
            crossref_client: Optional pre-configured CrossRefClient (for sharing).
            dblp_client: Optional pre-configured DBLPClient (for sharing).
            arxiv_client: Optional pre-configured ArxivClient (for sharing).
        """
        import os

        effective_api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.s2_client = s2_client or SemanticScholarClient(api_key=effective_api_key)
        self.crossref_client = crossref_client or CrossRefClient()
        self.dblp_client = dblp_client or DBLPClient()
        self.arxiv_client = arxiv_client or ArxivClient()
        # Track which clients we own (for proper cleanup)
        self._owns_s2 = s2_client is None
        self._owns_crossref = crossref_client is None
        self._owns_dblp = dblp_client is None
        self._owns_arxiv = arxiv_client is None

        self.skip_verified = skip_verified
        self.max_age_days = max_age_days
        self.auto_find_level = auto_find_level
        self.fix_mismatches = fix_mismatches
        self.console = console or Console()

        # Validate auto_find_level
        if auto_find_level not in (AUTO_FIND_NONE, AUTO_FIND_ID, AUTO_FIND_TITLE):
            raise ValueError(f"Invalid auto_find_level: {auto_find_level}")

    def close(self) -> None:
        """Close owned clients only."""
        if self._owns_s2:
            self.s2_client.close()
        if self._owns_crossref:
            self.crossref_client.close()
        if self._owns_dblp:
            self.dblp_client.close()
        # ArxivClient doesn't need closing (uses feedparser, no persistent connection)

    def __enter__(self) -> "BibVerifier":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _fetch_metadata(self, paper_id: str) -> PaperMetadata | None:
        """Fetch paper metadata. See verify_entry for flow documentation."""
        # Step 1: Resolve to DOI/arXiv ID + venue via S2
        resolved = self.s2_client.resolve_ids(paper_id)
        if not resolved:
            log.debug(f"Paper not found in Semantic Scholar: {paper_id}")
            return None

        log.info(f"Resolved: {paper_id} | DOI={resolved.doi} | arXiv={resolved.arxiv_id} | venue={resolved.venue}")

        # Case 1: DOI exists -> CrossRef
        if resolved.doi:
            log.info("Source: crossref (DOI exists)")
            crossref_meta = self.crossref_client.get_paper_metadata(resolved.doi)
            if crossref_meta:
                return PaperMetadata(
                    title=crossref_meta.title,
                    authors=crossref_meta.authors,
                    year=crossref_meta.year,
                    venue=crossref_meta.venue,
                    doi=crossref_meta.doi,
                    arxiv_id=resolved.arxiv_id,
                    source="crossref",
                )
            return None

        # Case 2: No DOI, venue != arXiv -> DBLP
        venue_is_arxiv = self._is_arxiv_venue(resolved.venue)
        if not venue_is_arxiv:
            log.info(f"Source: dblp (venue={resolved.venue})")
            if resolved.title:
                dblp_meta = self.dblp_client.search_by_title(resolved.title, resolved.venue)
                if dblp_meta:
                    return PaperMetadata(
                        title=dblp_meta.title,
                        authors=dblp_meta.authors,
                        year=dblp_meta.year,
                        venue=dblp_meta.venue,
                        doi=dblp_meta.doi,
                        arxiv_id=resolved.arxiv_id,
                        source="dblp",
                    )
            return None

        # Case 3: No DOI, venue == arXiv -> arXiv
        if resolved.arxiv_id:
            log.info("Source: arxiv")
            arxiv_meta = self.arxiv_client.get_paper_metadata(resolved.arxiv_id)
            if arxiv_meta:
                return PaperMetadata(
                    title=arxiv_meta.title,
                    authors=arxiv_meta.authors,
                    year=arxiv_meta.year,
                    venue=arxiv_meta.venue,
                    doi=resolved.doi,
                    arxiv_id=arxiv_meta.arxiv_id,
                    source="arxiv",
                )

        return None

    def _is_arxiv_venue(self, venue: str | None) -> bool:
        """Check if venue indicates arXiv preprint."""
        if not venue:
            return True  # No venue info, assume arXiv
        venue_lower = venue.lower()
        return "arxiv" in venue_lower or venue_lower in ("", "corr")

    def _should_skip_verified(self, date_str: str | None) -> bool:
        """Determine if a verified entry should be skipped based on age.

        Args:
            date_str: Verification date string in YYYY.MM.DD format.

        Returns:
            True if entry should be skipped, False if it should be re-verified.
        """
        # If max_age_days is None, always skip verified entries
        if self.max_age_days is None:
            return True

        # If max_age_days is 0, never skip (always re-verify)
        if self.max_age_days == 0:
            return False

        # If no date string, can't determine age - don't skip (re-verify)
        if not date_str:
            return False

        try:
            verified_date = datetime.strptime(date_str, "%Y.%m.%d")
            age_days = (datetime.now() - verified_date).days
            return age_days <= self.max_age_days
        except ValueError:
            # Invalid date format - don't skip (re-verify)
            return False

    def verify_entry(
        self,
        entry: dict,
        content: str,
    ) -> VerificationResult:
        """Verify a single bibtex entry.

        Flow:
        1. S2 resolves paper_id → DOI/arXiv ID + venue
        2. Source selection (mutually exclusive):
           - if DOI exists        → CrossRef
           - elif venue != arXiv  → DBLP
           - elif venue == arXiv  → arXiv
           - else                 → FAIL (return None)

        Args:
            entry: Bibtex entry dictionary.
            content: Raw file content for checking existing verification.

        Returns:
            Verification result.
        """
        entry_key = entry.get("ID", "unknown")

        # Check if already verified and should skip
        is_verified, date_str, _ = is_entry_verified(content, entry_key)
        if is_verified and self.skip_verified and self._should_skip_verified(date_str):
            return VerificationResult(
                entry_key=entry_key,
                success=True,
                message="Already verified",
                already_verified=True,
            )

        # Extract paper_id from entry (comment, doi/eprint depending on level)
        paper_id, source = extract_paper_id_from_entry(entry, content, self.auto_find_level)
        auto_found = source in ("doi", "eprint", "title") if source else False

        # If no paper_id and title search is enabled, try title search
        if not paper_id and self.auto_find_level == AUTO_FIND_TITLE:
            title = entry.get("title", "")
            if title:
                paper_id, source = self._search_by_title_for_id(entry)
                if paper_id:
                    auto_found = True

        # No paper_id = warning (not failure)
        if not paper_id:
            return VerificationResult(
                entry_key=entry_key,
                success=True,  # Not a failure, just a warning
                message="No paper_id found",
                no_paper_id=True,
            )

        # Delegate to common verification logic
        return self._verify_entry_with_metadata(entry, paper_id, source or "", auto_found)

    def _check_field_mismatches(
        self, entry: dict, metadata: PaperMetadata
    ) -> tuple[list[FieldMismatch], list[FieldMismatch]]:
        """Check for mismatches between bibtex entry and fetched metadata.

        Strict matching: only exact string match is PASS.
        - Exact match: PASS
        - Normalized/alias match: WARNING
        - No match: FAIL

        Args:
            entry: Bibtex entry dictionary.
            metadata: Paper metadata from CrossRef/arXiv.

        Returns:
            Tuple of (mismatches, warnings).
            - mismatches: Hard errors (FAIL).
            - warnings: Soft issues (WARNING).
        """
        source = metadata.source
        mismatches = []
        warnings = []

        # Check title
        bib_title = entry.get("title", "")
        if bib_title and metadata.title:
            match, warning_only = compare_titles(bib_title, metadata.title)
            if not match:
                mismatches.append(
                    FieldMismatch(
                        field_name="title",
                        bibtex_value=bib_title,
                        fetched_value=metadata.title,
                        source=source,
                        similarity=title_similarity(bib_title, metadata.title),
                        is_warning=False,
                    )
                )
            elif warning_only:
                warnings.append(
                    FieldMismatch(
                        field_name="title",
                        bibtex_value=bib_title,
                        fetched_value=metadata.title,
                        source=source,
                        is_warning=True,
                    )
                )

        # Check authors
        bib_author_field = entry.get("author", "")
        if bib_author_field and metadata.authors:
            api_author_str = metadata.get_authors_str()
            # compare_authors expects list of names, convert from dict format
            author_names = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in metadata.authors]
            match, warning_only = compare_authors(bib_author_field, author_names)
            if not match:
                mismatches.append(
                    FieldMismatch(
                        field_name="author",
                        bibtex_value=bib_author_field,
                        fetched_value=api_author_str,
                        source=source,
                        is_warning=False,
                    )
                )
            elif warning_only:
                warnings.append(
                    FieldMismatch(
                        field_name="author",
                        bibtex_value=bib_author_field,
                        fetched_value=api_author_str,
                        source=source,
                        is_warning=True,
                    )
                )

        # Check year (must be exact)
        bib_year = entry.get("year", "")
        if bib_year and metadata.year:
            try:
                bib_year_int = int(bib_year)
                if bib_year_int != metadata.year:
                    mismatches.append(
                        FieldMismatch(
                            field_name="year",
                            bibtex_value=str(bib_year_int),
                            fetched_value=str(metadata.year),
                            source=source,
                        )
                    )
            except ValueError:
                pass

        # Check venue
        bib_venue = entry.get("journal", "") or entry.get("booktitle", "")
        if bib_venue and metadata.venue:
            match, warning_only = compare_venues(bib_venue, metadata.venue)
            if not match:
                mismatches.append(
                    FieldMismatch(
                        field_name="venue",
                        bibtex_value=bib_venue,
                        fetched_value=metadata.venue,
                        source=source,
                        is_warning=False,
                    )
                )
            elif warning_only:
                warnings.append(
                    FieldMismatch(
                        field_name="venue",
                        bibtex_value=bib_venue,
                        fetched_value=metadata.venue,
                        source=source,
                        is_warning=True,
                    )
                )

        return mismatches, warnings

    def _search_by_title_for_id(self, entry: dict) -> tuple[str | None, str | None]:
        """Search for paper by title and return paper_id if found with high confidence.

        Uses S2 search to find a paper, then returns its paper_id for subsequent
        metadata lookup from CrossRef/arXiv.

        Args:
            entry: Bibtex entry dictionary.

        Returns:
            Tuple of (paper_id, source).
            - paper_id: S2 paper ID for subsequent resolve_ids() call
            - source: "title" if found, None otherwise
        """
        title = entry.get("title", "")
        if not title:
            return None, None

        # Strip LaTeX braces for search
        from .utils import strip_latex_braces

        search_title = strip_latex_braces(title)

        # Search by title via S2
        try:
            papers = self.s2_client.search_by_title(search_title, limit=3)
        except ConnectionError:
            return None, None

        if not papers:
            return None, None

        # Find best match by title similarity
        best_match = None
        best_score = 0.0
        for paper in papers:
            score = title_similarity(title, paper.title)
            if score > best_score:
                best_score = score
                best_match = paper

        if best_score >= 0.85 and best_match:
            return best_match.paper_id, "title"

        return None, None

    def verify_file(self, file_path: Path, show_progress: bool = True) -> tuple[VerificationReport, str]:
        """Verify all entries in a bibtex file.

        Args:
            file_path: Path to the .bib file.
            show_progress: Whether to show a progress bar.

        Returns:
            Tuple of (verification report, updated content).
        """
        from tqdm import tqdm

        entries, content = parse_bib_file(file_path)
        report = VerificationReport()
        updated_content = content

        # Collect entries to verify
        entries_to_verify: list[tuple[dict, str, str, bool]] = []  # (entry, paper_id, source, auto_found)
        for entry in entries:
            entry_key = entry.get("ID", "unknown")

            # Check if already verified and should skip
            is_verified, date_str, _ = is_entry_verified(content, entry_key)
            if is_verified and self.skip_verified and self._should_skip_verified(date_str):
                report.add_result(
                    VerificationResult(
                        entry_key=entry_key,
                        success=True,
                        message="Already verified",
                        already_verified=True,
                    )
                )
                continue

            # Extract paper_id
            paper_id, source = extract_paper_id_from_entry(entry, content, self.auto_find_level)
            auto_found = source in ("doi", "eprint", "title") if source else False

            # If no paper_id and title search is enabled, try title search
            if not paper_id and self.auto_find_level == AUTO_FIND_TITLE:
                title = entry.get("title", "")
                if title:
                    paper_id, source = self._search_by_title_for_id(entry)
                    if paper_id:
                        auto_found = True

            if not paper_id:
                report.add_result(
                    VerificationResult(
                        entry_key=entry_key,
                        success=True,
                        message="No paper_id found",
                        no_paper_id=True,
                    )
                )
                continue

            entries_to_verify.append((entry, paper_id, source or "", auto_found))

        if not entries_to_verify:
            return report, updated_content

        # Verify each entry
        if show_progress:
            self.console.print(f"[dim]Verifying {len(entries_to_verify)} entries...[/]")
            entry_iter = tqdm(entries_to_verify, desc="Verifying", unit="entry", leave=False)
        else:
            entry_iter = entries_to_verify

        for entry, paper_id, source, auto_found in entry_iter:
            result = self._verify_entry_with_metadata(entry, paper_id, source, auto_found)
            report.add_result(result)

            # Only mark as verified if PASS (success without warnings)
            is_pass = result.success and not result.warnings
            if is_pass and result.needs_update and result.metadata and result.paper_id_used:
                if result.fixed and result.mismatches:
                    updated_content = self._apply_field_fixes(
                        updated_content, entry, result.metadata, result.mismatches
                    )
                updated_content = self._add_verification_comment(updated_content, entry, result.paper_id_used)

        return report, updated_content

    def _verify_entry_with_metadata(
        self,
        entry: dict,
        paper_id: str,
        source: str,
        auto_found: bool,
    ) -> VerificationResult:
        """Verify entry by fetching metadata from CrossRef/arXiv.

        Args:
            entry: Bibtex entry dictionary.
            paper_id: Paper ID used for lookup.
            source: Source of paper_id.
            auto_found: Whether paper_id was auto-found.

        Returns:
            Verification result.
        """
        entry_key = entry.get("ID", "unknown")

        # Fetch metadata from CrossRef/arXiv
        try:
            metadata = self._fetch_metadata(paper_id)
        except Exception as e:
            return VerificationResult(
                entry_key=entry_key,
                success=False,
                message=f"API error: {e}",
                paper_id_used=paper_id,
                auto_found_paper_id=auto_found,
                paper_id_source=source,
            )

        if not metadata:
            return VerificationResult(
                entry_key=entry_key,
                success=False,
                message=f"Paper not found for {paper_id}",
                paper_id_used=paper_id,
                auto_found_paper_id=auto_found,
                paper_id_source=source,
            )

        # Verify title, authors, year, venue match
        mismatches, warnings = self._check_field_mismatches(entry, metadata)
        if mismatches:
            if self.fix_mismatches:
                return VerificationResult(
                    entry_key=entry_key,
                    success=True,
                    message="Fixed and verified",
                    metadata=metadata,
                    paper_id_used=paper_id,
                    auto_found_paper_id=auto_found,
                    paper_id_source=source,
                    mismatches=mismatches,
                    warnings=warnings,
                    fixed=True,
                    needs_update=True,
                )
            else:
                mismatch_fields = ", ".join(m.field_name for m in mismatches)
                return VerificationResult(
                    entry_key=entry_key,
                    success=False,
                    message=f"Field mismatch: {mismatch_fields}",
                    metadata=metadata,
                    paper_id_used=paper_id,
                    auto_found_paper_id=auto_found,
                    paper_id_source=source,
                    mismatches=mismatches,
                    warnings=warnings,
                )

        message = "Verified"
        if warnings:
            warning_fields = ", ".join(w.field_name for w in warnings)
            message = f"Verified (warning: {warning_fields} format differs)"

        return VerificationResult(
            entry_key=entry_key,
            success=True,
            message=message,
            metadata=metadata,
            paper_id_used=paper_id,
            auto_found_paper_id=auto_found,
            paper_id_source=source,
            warnings=warnings,
            needs_update=True,
        )

    def _add_verification_comment(
        self,
        content: str,
        entry: dict,
        paper_id: str,
    ) -> str:
        """Add a verification comment before an entry.

        Args:
            content: File content.
            entry: Bibtex entry dictionary.
            paper_id: Paper ID used for lookup. Required.

        Returns:
            Updated content with verification comment.
        """
        entry_key = entry.get("ID", "")
        # Find the entry in the content - capture leading whitespace, comments, then the entry
        # Pattern: whitespace, optional comments, then the entry
        entry_pattern = re.compile(
            rf"(\s*)((?:%[^\n]*\n)*)(@\w+\{{\s*{re.escape(entry_key)}\s*,)",
            re.MULTILINE,
        )
        match = entry_pattern.search(content)

        if not match:
            return content

        leading_whitespace = match.group(1)
        existing_comments = match.group(2).strip()
        entry_start = match.group(3)

        # Determine the prefix (what comes before this match)
        prefix = content[: match.start()]

        # Generate verification comment with paper_id embedded
        comment = generate_verification_comment(paper_id)

        # Remove existing paper_id comment if present (any format)
        # Matches: "% paper_id: xxx" or "% paper_id: xxx, verified via ..."
        existing_paper_id_pattern = re.compile(
            r"%\s*paper_id:\s*\S+[^\n]*\n?",
            re.IGNORECASE,
        )

        cleaned_comments = existing_paper_id_pattern.sub("", existing_comments)

        if cleaned_comments.strip():
            new_block = f"{leading_whitespace}{cleaned_comments.strip()}\n{comment}\n{entry_start}"
        else:
            new_block = f"{leading_whitespace}{comment}\n{entry_start}"

        return prefix + new_block + content[match.end() :]

    def _apply_field_fixes(
        self,
        content: str,
        entry: dict,
        metadata: PaperMetadata,
        mismatches: list[FieldMismatch],
    ) -> str:
        """Apply field fixes to an entry.

        Args:
            content: File content.
            entry: Bibtex entry dictionary.
            metadata: Paper metadata from CrossRef/arXiv.
            mismatches: List of field mismatches to fix.

        Returns:
            Updated content with fixed fields.
        """
        entry_key = entry.get("ID", "")

        # Find the full entry in content
        entry_pattern = re.compile(
            rf"(@\w+\{{\s*{re.escape(entry_key)}\s*,.*?\n\}})",
            re.DOTALL,
        )
        match = entry_pattern.search(content)
        if not match:
            return content

        entry_text = match.group(1)
        updated_entry = entry_text

        for mismatch in mismatches:
            field_name = mismatch.field_name
            new_value = mismatch.fetched_value

            if field_name == "title":
                # Replace title field
                updated_entry = self._replace_field(updated_entry, "title", metadata.title or "")
            elif field_name == "author":
                # Replace author field
                authors_str = metadata.get_authors_str()
                updated_entry = self._replace_field(updated_entry, "author", authors_str)
            elif field_name == "year":
                # Replace year field
                updated_entry = self._replace_field(updated_entry, "year", str(metadata.year or ""))
            elif field_name == "venue":
                # Replace journal or booktitle
                if "journal" in entry:
                    updated_entry = self._replace_field(updated_entry, "journal", new_value)
                elif "booktitle" in entry:
                    updated_entry = self._replace_field(updated_entry, "booktitle", new_value)

        return content[: match.start()] + updated_entry + content[match.end() :]

    def _replace_field(self, entry_text: str, field_name: str, new_value: str) -> str:
        """Replace a field value in an entry.

        Args:
            entry_text: The bibtex entry text.
            field_name: Name of the field to replace.
            new_value: New value for the field.

        Returns:
            Updated entry text.
        """
        # Match field = {value} or field = "value" or field = value
        # Handle multi-line values properly
        field_pattern = re.compile(
            rf"(\s*)({re.escape(field_name)}\s*=\s*)(\{{[^}}]*\}}|\"[^\"]*\"|[^,\n]+)",
            re.IGNORECASE,
        )
        match = field_pattern.search(entry_text)
        if match:
            indent = match.group(1)
            field_prefix = match.group(2)
            # Use braces for the new value
            new_field = f"{indent}{field_prefix}{{{new_value}}}"
            return entry_text[: match.start()] + new_field + entry_text[match.end() :]
        return entry_text
