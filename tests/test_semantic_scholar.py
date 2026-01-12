"""Tests for Semantic Scholar API client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from bibtools.semantic_scholar import SemanticScholarClient


class TestSemanticScholarClientInit:
    """Tests for client initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = SemanticScholarClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client._rate_limiter.min_interval == 1.0  # With key

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = SemanticScholarClient()
        assert client.api_key is None
        assert client._rate_limiter.min_interval == 3.0  # Without key

    def test_get_headers_with_key(self):
        """Test headers include API key when provided."""
        client = SemanticScholarClient(api_key="test_key_headers")
        headers = client._get_headers()
        assert headers["x-api-key"] == "test_key_headers"
        assert headers["Accept"] == "application/json"

    def test_get_headers_without_key(self):
        """Test headers without API key."""
        client = SemanticScholarClient()
        headers = client._get_headers()
        assert "x-api-key" not in headers
        assert headers["Accept"] == "application/json"


class TestParsePaper:
    """Tests for paper parsing."""

    def test_parse_complete_paper(self):
        """Test parsing a complete paper response - all fields from bibtex."""
        client = SemanticScholarClient(api_key="test_parse_1")
        bibtex = """@inproceedings{Smith2024Test,
  author = {John Smith and Jane Doe},
  title = {Test Paper Title},
  booktitle = {Advances in Neural Information Processing Systems},
  year = {2024}
}"""
        data = {"paperId": "abc123", "citationStyles": {"bibtex": bibtex}}
        paper = client._parse_paper(data)
        assert paper.paper_id == "abc123"
        assert paper.title == "Test Paper Title"
        # Authors are formatted to bibtex style: Lastname, Firstname
        assert paper.authors == ["Smith, John", "Doe, Jane"]
        assert paper.year == 2024
        assert paper.venue == "Advances in Neural Information Processing Systems"

    def test_parse_article_with_journal(self):
        """Test parsing article - venue from journal field."""
        client = SemanticScholarClient(api_key="test_parse_article")
        bibtex = "@article{x,\n  title = {Test},\n  journal = {Nature},\n  year = {2023}\n}"
        data = {"paperId": "abc", "citationStyles": {"bibtex": bibtex}}
        paper = client._parse_paper(data)
        assert paper.venue == "Nature"
        assert paper.year == 2023

    def test_parse_minimal_paper(self):
        """Test parsing paper with minimal bibtex."""
        client = SemanticScholarClient(api_key="test_parse_2")
        data = {
            "paperId": "abc",
            "citationStyles": {"bibtex": "@article{x,\n  title = {Minimal}\n}"},
        }
        paper = client._parse_paper(data)
        assert paper.paper_id == "abc"
        assert paper.title == "Minimal"
        assert paper.authors == []
        assert paper.year is None
        assert paper.venue is None

    def test_parse_paper_no_bibtex(self):
        """Test parsing paper with no bibtex available returns None."""
        client = SemanticScholarClient(api_key="test_parse_3")
        data = {"paperId": "abc", "citationStyles": None}
        paper = client._parse_paper(data)
        # Bibtex parsing failure -> None (conservative approach)
        assert paper is None

    def test_parse_paper_no_paper_id(self):
        """Test parsing paper with no paper_id returns None."""
        client = SemanticScholarClient(api_key="test_parse_4")
        data = {"paperId": "", "citationStyles": {"bibtex": "@article{x, title={Test}}"}}
        paper = client._parse_paper(data)
        assert paper is None


class TestSearchByTitle:
    """Tests for search_by_title method."""

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_search_success(self, mock_request):
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "paperId": "1",
                    "citationStyles": {"bibtex": "@article{p1, title={Paper One}, year={2024}}"},
                },
                {
                    "paperId": "2",
                    "citationStyles": {"bibtex": "@article{p2, title={Paper Two}, year={2023}}"},
                },
            ]
        }
        mock_request.return_value = mock_response

        client = SemanticScholarClient(api_key="test_search_1")
        results = client.search_by_title("machine learning", limit=5)

        assert len(results) == 2
        assert results[0].paper_id == "1"
        assert results[1].paper_id == "2"

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_search_empty_results(self, mock_request):
        """Test search with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_request.return_value = mock_response

        client = SemanticScholarClient(api_key="test_search_2")
        results = client.search_by_title("nonexistent paper xyz", limit=5)

        assert len(results) == 0

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_search_cleans_latex(self, mock_request):
        """Test that search cleans LaTeX braces from title."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_request.return_value = mock_response

        client = SemanticScholarClient(api_key="test_search_3")
        client.search_by_title("{CNN} for {NLP}")

        call_args = mock_request.call_args
        params = call_args.kwargs.get("params", {})
        assert "{" not in params["query"]
        assert "}" not in params["query"]

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_search_http_error(self, mock_request):
        """Test search with HTTP error."""
        mock_request.side_effect = httpx.HTTPError("Connection failed")

        client = SemanticScholarClient(api_key="test_search_4")
        with pytest.raises(ConnectionError, match="Failed to search"):
            client.search_by_title("test")

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_search_excludes_abbreviated_authors(self, mock_request):
        """Test that papers with abbreviated authors are excluded."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "paperId": "1",
                    "citationStyles": {"bibtex": "@article{p1, title={Paper One}, author={A. Smith}, year={2024}}"},
                },
                {
                    "paperId": "2",
                    "citationStyles": {"bibtex": "@article{p2, title={Paper Two}, year={2023}}"},
                },
            ]
        }
        mock_request.return_value = mock_response

        client = SemanticScholarClient(api_key="test_search_5")
        results = client.search_by_title("test", limit=5)

        # Paper 1 has abbreviated author "A. Smith" -> excluded
        # Paper 2 has no authors -> included
        assert len(results) == 1
        assert results[0].paper_id == "2"


class TestGetPaper:
    """Tests for get_paper method."""

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_get_paper_by_arxiv_id(self, mock_request):
        """Test getting paper by arXiv ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "paperId": "abc123",
            "citationStyles": {
                "bibtex": "@article{x,\n  title = {ArXiv Paper},\n  author = {Author},\n  year = {2024}\n}"
            },
        }
        mock_request.return_value = mock_response

        client = SemanticScholarClient(api_key="test_get_1")
        paper = client.get_paper("ARXIV:2406.09246")

        assert paper is not None
        assert paper.title == "ArXiv Paper"
        mock_request.assert_called_once()
        assert "ARXIV:2406.09246" in str(mock_request.call_args)

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_get_paper_by_doi(self, mock_request):
        """Test getting paper by DOI."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "paperId": "abc123",
            "citationStyles": {"bibtex": "@article{x,\n  title = {DOI Paper},\n  year = {2024}\n}"},
        }
        mock_request.return_value = mock_response

        client = SemanticScholarClient(api_key="test_get_2")
        paper = client.get_paper("DOI:10.1234/test")

        assert paper is not None
        assert paper.title == "DOI Paper"

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_get_paper_not_found(self, mock_request):
        """Test getting non-existent paper."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
        mock_request.side_effect = error

        client = SemanticScholarClient(api_key="test_get_3")
        paper = client.get_paper("ARXIV:0000.00000")

        assert paper is None

    @patch.object(SemanticScholarClient, "_request_with_retry")
    def test_get_paper_http_error(self, mock_request):
        """Test get_paper with HTTP error (non-404)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        mock_request.side_effect = error

        client = SemanticScholarClient(api_key="test_get_4")
        with pytest.raises(ConnectionError, match="Failed to get paper"):
            client.get_paper("ARXIV:2406.09246")
