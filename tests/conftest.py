"""Pytest configuration and fixtures."""

import os
from pathlib import Path
from typing import Callable

import pytest

from bibtools.models import BibtexEntry, PaperInfo, PaperMetadata


@pytest.fixture
def make_paper() -> Callable[..., PaperInfo]:
    """Fixture factory to create PaperInfo with BibtexEntry."""

    def _make_paper(
        paper_id: str,
        title: str = "",
        authors: list[str] | None = None,
        venue: str | None = None,
        year: int | None = None,
        entry_type: str = "inproceedings",
    ) -> PaperInfo:
        bibtex = BibtexEntry(
            key=paper_id,
            title=title,
            authors=authors or [],
            venue=venue,
            year=year,
            entry_type=entry_type,
        )
        return PaperInfo(paper_id=paper_id, bibtex=bibtex)

    return _make_paper


@pytest.fixture
def make_metadata() -> Callable[..., PaperMetadata]:
    """Fixture factory to create PaperMetadata for testing."""

    def _make_metadata(
        title: str = "",
        authors: list[str] | None = None,
        venue: str | None = None,
        year: int | None = None,
        source: str = "crossref",
        doi: str | None = None,
        arxiv_id: str | None = None,
    ) -> PaperMetadata:
        # Convert simple author list to dict format
        author_dicts = []
        for author in authors or []:
            parts = author.split()
            if len(parts) >= 2:
                author_dicts.append({"given": " ".join(parts[:-1]), "family": parts[-1]})
            else:
                author_dicts.append({"given": "", "family": author})
        return PaperMetadata(
            title=title,
            authors=author_dicts,
            venue=venue,
            year=year,
            source=source,
            doi=doi,
            arxiv_id=arxiv_id,
        )

    return _make_metadata


@pytest.fixture(autouse=True)
def load_env():
    """Load environment variables from .env file for tests."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
    yield
