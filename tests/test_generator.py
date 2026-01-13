"""Tests for bibtex generator module."""

from unittest.mock import MagicMock, patch

from bibtools.generator import BibtexGenerator
from bibtools.models import BibtexEntry


class TestBibtexEntry:
    """Tests for BibtexEntry class."""

    def test_from_raw_bibtex_inproceedings(self):
        """Test parsing inproceedings entry."""
        raw = """@inproceedings{Vaswani2017,
  author = {Ashish Vaswani and Noam Shazeer},
  booktitle = {NeurIPS},
  title = {Attention is All you Need},
  year = {2017}
}"""
        entry = BibtexEntry.from_raw_bibtex(raw)
        assert entry is not None
        assert entry.key == "Vaswani2017"
        assert entry.title == "Attention is All you Need"
        assert entry.authors == ["Ashish Vaswani", "Noam Shazeer"]
        assert entry.venue == "NeurIPS"
        assert entry.year == 2017
        assert entry.entry_type == "inproceedings"

    def test_from_raw_bibtex_article(self):
        """Test parsing article entry."""
        raw = """@article{Test2024,
  author = {John Smith},
  journal = {Nature},
  title = {Test Paper},
  year = {2024}
}"""
        entry = BibtexEntry.from_raw_bibtex(raw)
        assert entry is not None
        assert entry.entry_type == "article"
        assert entry.venue == "Nature"

    def test_from_raw_bibtex_invalid(self):
        """Test parsing invalid bibtex returns None."""
        assert BibtexEntry.from_raw_bibtex("") is None
        assert BibtexEntry.from_raw_bibtex("not bibtex") is None

    def test_to_bibtex_field_order(self):
        """Test serialization has correct field order: title, author, venue, year."""
        entry = BibtexEntry(
            key="test2024",
            title="Test Paper",
            authors=["John Smith"],
            venue="Conference",
            year=2024,
        )
        bibtex = entry.to_bibtex()
        assert bibtex.index("  title") < bibtex.index("  author")
        assert bibtex.index("  author") < bibtex.index("  booktitle")
        assert bibtex.index("  booktitle") < bibtex.index("  year")

    def test_to_bibtex_with_paper_id(self):
        """Test serialization includes paper_id comment."""
        entry = BibtexEntry(
            key="test",
            title="Test",
            authors=["Author"],
            venue=None,
            year=2024,
        )
        bibtex = entry.to_bibtex("ARXIV:2106.15928")
        assert "% paper_id: ARXIV:2106.15928" in bibtex

    def test_to_bibtex_article_uses_journal(self):
        """Test article entries use journal field."""
        entry = BibtexEntry(
            key="test",
            title="Test",
            authors=[],
            venue="Nature",
            year=2024,
            entry_type="article",
        )
        bibtex = entry.to_bibtex()
        assert "journal = {Nature}" in bibtex
        assert "booktitle" not in bibtex


class TestPaperInfo:
    """Tests for PaperInfo class."""

    def test_properties_from_bibtex(self, make_paper):
        """Test that properties are delegated to bibtex."""
        paper = make_paper(
            paper_id="abc",
            title="Test Paper",
            authors=["John Smith"],
            venue="NeurIPS",
            year=2024,
        )
        assert paper.title == "Test Paper"
        assert paper.authors == ["John Smith"]
        assert paper.venue == "NeurIPS"
        assert paper.year == 2024


class TestBibtexGenerator:
    """Tests for BibtexGenerator class."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        generator = BibtexGenerator(api_key="test_key")
        assert generator._fetcher is not None

    @patch.object(BibtexGenerator, "__init__", lambda self, **kwargs: None)
    def test_fetch_by_paper_id_success(self):
        """Test fetching bibtex by paper_id with new architecture."""
        from bibtools.models import PaperMetadata

        generator = BibtexGenerator.__new__(BibtexGenerator)
        generator._fetcher = MagicMock()

        # Mock fetcher.fetch
        generator._fetcher.fetch.return_value = PaperMetadata(
            title="Test Paper",
            authors=[{"given": "John", "family": "Doe"}],
            venue="Test Conference",
            year=2024,
            doi="10.1234/test",
            source="crossref",
        )

        result = generator.fetch_by_paper_id("ARXIV:2106.15928")
        assert result is not None
        assert "Test Paper" in result.bibtex
        assert "% paper_id: ARXIV:2106.15928" in result.bibtex

    @patch.object(BibtexGenerator, "__init__", lambda self, **kwargs: None)
    def test_fetch_by_paper_id_not_found(self):
        """Test fetching non-existent paper."""
        generator = BibtexGenerator.__new__(BibtexGenerator)
        generator._fetcher = MagicMock()
        generator._fetcher.fetch.return_value = None

        result = generator.fetch_by_paper_id("ARXIV:0000.00000")
        assert result is None

    @patch.object(BibtexGenerator, "__init__", lambda self, **kwargs: None)
    def test_search_by_query(self, make_paper):
        """Test search by query (uses legacy flow)."""
        generator = BibtexGenerator.__new__(BibtexGenerator)
        generator._fetcher = MagicMock()
        generator._fetcher.s2_client = MagicMock()
        generator._fetcher.s2_client.search_by_title.return_value = [
            make_paper(paper_id="paper1", title="ML Paper", authors=["Author"], year=2024),
        ]

        results = generator.search_by_query("machine learning", limit=5)
        assert len(results) == 1
        bibtex, paper = results[0]
        assert "ML Paper" in bibtex
        assert paper.title == "ML Paper"
