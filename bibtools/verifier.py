"""Core verification logic."""

import re
from datetime import datetime
from pathlib import Path

from rich.console import Console

from .constants import AUTO_FIND_ID, AUTO_FIND_NONE, AUTO_FIND_TITLE
from .models import FieldMismatch, PaperInfo, VerificationReport, VerificationResult
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


def find_best_match(entry_title: str, papers: list[PaperInfo]) -> PaperInfo | None:
    """Find the best matching paper from a list.

    Args:
        entry_title: Title from bibtex entry.
        papers: List of papers from Semantic Scholar.

    Returns:
        Best matching paper if similarity > 0.85, None otherwise.
    """
    if not papers:
        return None

    best_match = None
    best_score = 0.0

    for paper in papers:
        score = title_similarity(entry_title, paper.title)
        if score > best_score:
            best_score = score
            best_match = paper

    if best_score >= 0.85:
        return best_match

    return None


class BibVerifier:
    """Verifies bibtex entries using Semantic Scholar."""

    def __init__(
        self,
        api_key: str | None = None,
        skip_verified: bool = True,
        max_age_days: int | None = None,
        auto_find_level: str = "id",
        fix_mismatches: bool = False,
        console: Console | None = None,
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
        """
        import os

        effective_api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self.client = SemanticScholarClient(api_key=effective_api_key)
        self.skip_verified = skip_verified
        self.max_age_days = max_age_days
        self.auto_find_level = auto_find_level
        self.fix_mismatches = fix_mismatches
        self.console = console or Console()

        # Validate auto_find_level
        if auto_find_level not in (AUTO_FIND_NONE, AUTO_FIND_ID, AUTO_FIND_TITLE):
            raise ValueError(f"Invalid auto_find_level: {auto_find_level}")

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
        # Title search returns paper_info directly, avoiding a second API call
        paper_info: PaperInfo | None = None
        if not paper_id and self.auto_find_level == AUTO_FIND_TITLE:
            title = entry.get("title", "")
            if title:
                paper_id, source, paper_info = self._search_by_title(entry)
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

        # Lookup paper by paper_id (skip if already have paper_info from title search)
        if paper_info is None:
            try:
                paper_info = self.client.get_paper(paper_id)
            except ConnectionError as e:
                return VerificationResult(
                    entry_key=entry_key,
                    success=False,
                    message=f"API error: {e}",
                    paper_id_used=paper_id,
                    auto_found_paper_id=auto_found,
                    paper_id_source=source,
                )

        if not paper_info:
            return VerificationResult(
                entry_key=entry_key,
                success=False,
                message=f"Paper not found for {paper_id}",
                paper_id_used=paper_id,
                auto_found_paper_id=auto_found,
                paper_id_source=source,
            )

        # Verify title, authors, year, venue match
        mismatches, warnings = self._check_field_mismatches(entry, paper_info)
        if mismatches:
            # If fix_mismatches is enabled, mark as fixable instead of failed
            if self.fix_mismatches:
                return VerificationResult(
                    entry_key=entry_key,
                    success=True,  # Considered success because we'll fix it
                    message="Fixed and verified",
                    paper_info=paper_info,
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
                    paper_info=paper_info,
                    paper_id_used=paper_id,
                    auto_found_paper_id=auto_found,
                    paper_id_source=source,
                    mismatches=mismatches,
                    warnings=warnings,
                )

        # Success (with possible warnings)
        message = "Verified"
        if warnings:
            warning_fields = ", ".join(w.field_name for w in warnings)
            message = f"Verified (warning: {warning_fields} format differs)"

        # Always update on successful verification
        # (if we reached here, we didn't skip - either new or re-verifying)
        return VerificationResult(
            entry_key=entry_key,
            success=True,
            message=message,
            paper_info=paper_info,
            paper_id_used=paper_id,
            auto_found_paper_id=auto_found,
            paper_id_source=source,
            warnings=warnings,
            needs_update=True,
        )

    def _check_field_mismatches(
        self, entry: dict, paper_info: PaperInfo
    ) -> tuple[list[FieldMismatch], list[FieldMismatch]]:
        """Check for mismatches between bibtex entry and Semantic Scholar data.

        Strict matching: only exact string match is PASS.
        - Exact match: PASS
        - Normalized/alias match: WARNING
        - No match: FAIL

        Args:
            entry: Bibtex entry dictionary.
            paper_info: Paper information from Semantic Scholar.

        Returns:
            Tuple of (mismatches, warnings).
            - mismatches: Hard errors (FAIL).
            - warnings: Soft issues (WARNING).
        """
        mismatches = []
        warnings = []

        # Check title
        bib_title = entry.get("title", "")
        if bib_title and paper_info.title:
            match, warning_only = compare_titles(bib_title, paper_info.title)
            if not match:
                mismatches.append(
                    FieldMismatch(
                        field_name="title",
                        bibtex_value=bib_title,
                        semantic_scholar_value=paper_info.title,
                        similarity=title_similarity(bib_title, paper_info.title),
                        is_warning=False,
                    )
                )
            elif warning_only:
                warnings.append(
                    FieldMismatch(
                        field_name="title",
                        bibtex_value=bib_title,
                        semantic_scholar_value=paper_info.title,
                        is_warning=True,
                    )
                )

        # Check authors
        bib_author_field = entry.get("author", "")
        if bib_author_field and paper_info.authors:
            ss_author_str = " and ".join(paper_info.authors)
            match, warning_only = compare_authors(bib_author_field, paper_info.authors)
            if not match:
                mismatches.append(
                    FieldMismatch(
                        field_name="author",
                        bibtex_value=bib_author_field,
                        semantic_scholar_value=ss_author_str,
                        is_warning=False,
                    )
                )
            elif warning_only:
                warnings.append(
                    FieldMismatch(
                        field_name="author",
                        bibtex_value=bib_author_field,
                        semantic_scholar_value=ss_author_str,
                        is_warning=True,
                    )
                )

        # Check year (must be exact)
        bib_year = entry.get("year", "")
        if bib_year and paper_info.year:
            try:
                bib_year_int = int(bib_year)
                if bib_year_int != paper_info.year:
                    mismatches.append(
                        FieldMismatch(
                            field_name="year",
                            bibtex_value=str(bib_year_int),
                            semantic_scholar_value=str(paper_info.year),
                        )
                    )
            except ValueError:
                pass

        # Check venue
        bib_venue = entry.get("journal", "") or entry.get("booktitle", "")
        if bib_venue and paper_info.venue:
            match, warning_only = compare_venues(bib_venue, paper_info.venue)
            if not match:
                mismatches.append(
                    FieldMismatch(
                        field_name="venue",
                        bibtex_value=bib_venue,
                        semantic_scholar_value=paper_info.venue,
                        is_warning=False,
                    )
                )
            elif warning_only:
                warnings.append(
                    FieldMismatch(
                        field_name="venue",
                        bibtex_value=bib_venue,
                        semantic_scholar_value=paper_info.venue,
                        is_warning=True,
                    )
                )

        return mismatches, warnings

    def _search_by_title(self, entry: dict) -> tuple[str | None, str | None, PaperInfo | None]:
        """Search for paper by title and return paper_id if found with high confidence.

        Args:
            entry: Bibtex entry dictionary.

        Returns:
            Tuple of (paper_id, source, paper_info).
            - paper_id: Canonical paper ID (ARXIV:xxx or DOI:xxx)
            - source: "title" if found, None otherwise
            - paper_info: PaperInfo from search (avoids second API call)
        """
        title = entry.get("title", "")
        if not title:
            return None, None, None

        # Strip LaTeX braces for search
        from .utils import strip_latex_braces

        search_title = strip_latex_braces(title)

        # Search by title
        try:
            papers = self.client.search_by_title(search_title, limit=3)
        except ConnectionError:
            return None, None, None

        if not papers:
            return None, None, None

        # Find best match
        best_match = find_best_match(title, papers)
        if not best_match:
            return None, None, None

        # Use Semantic Scholar paper_id
        return best_match.paper_id, "title", best_match

    def verify_file(self, file_path: Path, show_progress: bool = True) -> tuple[VerificationReport, str]:
        """Verify all entries in a bibtex file using batch API.

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

        # Phase 1: Collect paper_ids to fetch
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

        # Phase 2: Batch fetch all papers
        paper_ids = [paper_id for _, paper_id, _, _ in entries_to_verify]
        if show_progress:
            self.console.print(f"[dim]Fetching {len(paper_ids)} papers via batch API...[/]")

        try:
            papers_map = self.client.get_papers_batch(paper_ids)
        except ConnectionError as e:
            # If batch fails, fall back to individual requests
            self.console.print(f"[yellow]Batch API failed, falling back to individual requests: {e}[/]")
            papers_map = {}
            for paper_id in paper_ids:
                try:
                    papers_map[paper_id] = self.client.get_paper(paper_id)
                except ConnectionError:
                    papers_map[paper_id] = None

        # Phase 3: Verify each entry with fetched data
        if show_progress and len(entries_to_verify) > 0:
            entry_iter = tqdm(entries_to_verify, desc="Verifying", unit="entry", leave=False)
        else:
            entry_iter = entries_to_verify

        for entry, paper_id, source, auto_found in entry_iter:
            result = self._verify_entry_with_paper(entry, paper_id, source, auto_found, papers_map.get(paper_id))
            report.add_result(result)

            # Only mark as verified if PASS (success without warnings)
            is_pass = result.success and not result.warnings
            if is_pass and result.needs_update and result.paper_info and result.paper_id_used:
                if result.fixed and result.mismatches:
                    updated_content = self._apply_field_fixes(
                        updated_content, entry, result.paper_info, result.mismatches
                    )
                updated_content = self._add_verification_comment(updated_content, entry, result.paper_id_used)

        return report, updated_content

    def _verify_entry_with_paper(
        self,
        entry: dict,
        paper_id: str,
        source: str,
        auto_found: bool,
        paper_info: PaperInfo | None,
    ) -> VerificationResult:
        """Verify entry with pre-fetched paper info.

        Args:
            entry: Bibtex entry dictionary.
            paper_id: Paper ID used for lookup.
            source: Source of paper_id.
            auto_found: Whether paper_id was auto-found.
            paper_info: Pre-fetched paper info (or None if not found).

        Returns:
            Verification result.
        """
        entry_key = entry.get("ID", "unknown")

        if not paper_info:
            return VerificationResult(
                entry_key=entry_key,
                success=False,
                message=f"Paper not found for {paper_id}",
                paper_id_used=paper_id,
                auto_found_paper_id=auto_found,
                paper_id_source=source,
            )

        # Verify title, authors, year, venue match
        mismatches, warnings = self._check_field_mismatches(entry, paper_info)
        if mismatches:
            if self.fix_mismatches:
                return VerificationResult(
                    entry_key=entry_key,
                    success=True,
                    message="Fixed and verified",
                    paper_info=paper_info,
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
                    paper_info=paper_info,
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
            paper_info=paper_info,
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
        paper_info: PaperInfo,
        mismatches: list[FieldMismatch],
    ) -> str:
        """Apply field fixes to an entry.

        Args:
            content: File content.
            entry: Bibtex entry dictionary.
            paper_info: Paper information from Semantic Scholar.
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
            new_value = mismatch.semantic_scholar_value

            if field_name == "title":
                # Replace title field
                updated_entry = self._replace_field(updated_entry, "title", paper_info.title)
            elif field_name == "author":
                # Replace author field
                authors_str = " and ".join(paper_info.authors)
                updated_entry = self._replace_field(updated_entry, "author", authors_str)
            elif field_name == "year":
                # Replace year field
                updated_entry = self._replace_field(updated_entry, "year", str(paper_info.year))
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
