"""Tests for arxiv_mcp.server module."""

import random
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from arxiv_mcp.models import Paper, SearchResult, ExportConfig
from arxiv_mcp.server import ArxivMCPServer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api():
    api = AsyncMock()
    return api


@pytest.fixture
def server(mock_api):
    """ArxivMCPServer with a mocked ArxivAPI."""
    srv = ArxivMCPServer()
    srv.api = mock_api
    # Re-wire sub-components that reference the API
    srv.trend_analyzer.api = mock_api
    srv.related_finder.api = mock_api
    return srv


@pytest.fixture
def two_papers():
    return [
        Paper(
            id="2401.00001",
            title="Paper One on AI",
            authors=["Alice Smith"],
            abstract="Abstract one.",
            categories=["cs.AI"],
            published="2024-01-01",
            arxiv_url="https://arxiv.org/abs/2401.00001",
            pdf_url="https://arxiv.org/pdf/2401.00001",
        ),
        Paper(
            id="2401.00002",
            title="Paper Two on ML",
            authors=["Bob Jones"],
            abstract="Abstract two.",
            categories=["cs.LG"],
            published="2024-01-05",
            arxiv_url="https://arxiv.org/abs/2401.00002",
            pdf_url="https://arxiv.org/pdf/2401.00002",
        ),
    ]


# ---------------------------------------------------------------------------
# get_tools
# ---------------------------------------------------------------------------


class TestGetTools:

    def test_returns_all_tools(self, server):
        tools = server.get_tools()
        tool_names = {t.name for t in tools}
        expected = {
            "search_arxiv", "get_paper", "summarize_paper",
            "search_by_author", "search_by_category", "get_recent_papers",
            "compare_papers", "find_related_papers", "get_paper_citations",
            "analyze_trends", "export_papers",
        }
        assert expected == tool_names

    def test_tools_have_input_schemas(self, server):
        for tool in server.get_tools():
            assert tool.inputSchema is not None
            assert "properties" in tool.inputSchema


# ---------------------------------------------------------------------------
# search_arxiv
# ---------------------------------------------------------------------------


class TestSearchArxiv:

    async def test_success(self, server, mock_api, sample_papers):
        mock_api.search.return_value = SearchResult(
            query="test", total_results=5, papers=sample_papers
        )

        result = await server.search_arxiv("test", max_results=10)

        assert result["query"] == "test"
        assert result["total_results"] == 5
        assert len(result["papers"]) == 5
        assert result["error"] is None

    async def test_api_exception(self, server, mock_api):
        mock_api.search.side_effect = RuntimeError("boom")

        result = await server.search_arxiv("test")

        assert "error" in result
        assert result["papers"] == []

    async def test_passes_sort_by(self, server, mock_api):
        mock_api.search.return_value = SearchResult(
            query="q", total_results=0, papers=[]
        )

        await server.search_arxiv("q", sort_by="submittedDate")
        mock_api.search.assert_awaited_with("q", 10, "submittedDate")


# ---------------------------------------------------------------------------
# get_paper
# ---------------------------------------------------------------------------


class TestGetPaper:

    async def test_found(self, server, mock_api, sample_paper):
        mock_api.get_paper.return_value = sample_paper

        result = await server.get_paper("2401.00001")

        assert result["id"] == "2401.00001"
        assert result["title"] == sample_paper.title

    async def test_not_found(self, server, mock_api):
        mock_api.get_paper.return_value = None

        result = await server.get_paper("9999.99999")
        assert result == {"error": "Paper not found"}

    async def test_exception(self, server, mock_api):
        mock_api.get_paper.side_effect = RuntimeError("fail")

        result = await server.get_paper("2401.00001")
        assert "error" in result


# ---------------------------------------------------------------------------
# summarize_paper
# ---------------------------------------------------------------------------


class TestSummarizePaper:

    async def test_found(self, server, mock_api, sample_paper):
        mock_api.get_paper.return_value = sample_paper

        result = await server.summarize_paper("2401.00001")

        assert sample_paper.title in result
        assert "Abstract" in result

    async def test_not_found(self, server, mock_api):
        mock_api.get_paper.return_value = None

        result = await server.summarize_paper("9999.99999")
        assert "Error" in result

    async def test_exception(self, server, mock_api):
        mock_api.get_paper.side_effect = RuntimeError("fail")

        result = await server.summarize_paper("2401.00001")
        assert "Error" in result


# ---------------------------------------------------------------------------
# search_by_author
# ---------------------------------------------------------------------------


class TestSearchByAuthor:

    async def test_success(self, server, mock_api, sample_papers):
        mock_api.search.return_value = SearchResult(
            query='au:"Hinton"', total_results=2, papers=sample_papers[:2]
        )

        result = await server.search_by_author("Hinton", max_results=2)

        assert "papers" in result
        # Verify the query was built with author syntax
        call_query = mock_api.search.call_args[0][0]
        assert "au:" in call_query

    async def test_exception(self, server, mock_api):
        mock_api.search.side_effect = RuntimeError("fail")

        result = await server.search_by_author("Hinton")
        assert "error" in result


# ---------------------------------------------------------------------------
# search_by_category
# ---------------------------------------------------------------------------


class TestSearchByCategory:

    async def test_success(self, server, mock_api, sample_papers):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=2, papers=sample_papers[:2]
        )

        result = await server.search_by_category("cs.AI")

        call_query = mock_api.search.call_args[0][0]
        assert "cat:cs.AI" in call_query

    async def test_exception(self, server, mock_api):
        mock_api.search.side_effect = RuntimeError("fail")
        result = await server.search_by_category("cs.AI")
        assert "error" in result


# ---------------------------------------------------------------------------
# get_recent_papers
# ---------------------------------------------------------------------------


class TestGetRecentPapers:

    async def test_without_category(self, server, mock_api):
        mock_api.search.return_value = SearchResult(
            query="date", total_results=0, papers=[]
        )

        result = await server.get_recent_papers(days_back=3, max_results=5)

        call_query = mock_api.search.call_args[0][0]
        assert "submittedDate:" in call_query
        assert "cat:" not in call_query

    async def test_with_category(self, server, mock_api):
        mock_api.search.return_value = SearchResult(
            query="date+cat", total_results=0, papers=[]
        )

        result = await server.get_recent_papers(category="cs.LG", days_back=7)

        call_query = mock_api.search.call_args[0][0]
        assert "cat:cs.LG" in call_query
        assert "submittedDate:" in call_query

    async def test_exception(self, server, mock_api):
        mock_api.search.side_effect = RuntimeError("fail")
        result = await server.get_recent_papers()
        assert "error" in result


# ---------------------------------------------------------------------------
# compare_papers
# ---------------------------------------------------------------------------


class TestComparePapers:

    async def test_success(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.compare_papers(
            ["2401.00001", "2401.00002"],
            comparison_fields=["authors", "published"],
        )

        assert "Paper 1" in result
        assert "Paper 2" in result
        assert "Authors" in result

    async def test_no_valid_papers(self, server, mock_api):
        mock_api.get_paper.return_value = None

        result = await server.compare_papers(["bad1", "bad2"])
        assert "Error" in result

    async def test_default_fields(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.compare_papers(["2401.00001", "2401.00002"])
        # Default includes authors, categories, abstract, published
        assert "Authors" in result
        assert "Categories" in result

    async def test_exception(self, server, mock_api):
        mock_api.get_paper.side_effect = RuntimeError("fail")
        result = await server.compare_papers(["id1", "id2"])
        assert "Error" in result


# ---------------------------------------------------------------------------
# find_related_papers
# ---------------------------------------------------------------------------


class TestFindRelatedPapers:

    async def test_success(self, server, mock_api, sample_paper, sample_papers):
        mock_api.get_paper.return_value = sample_paper
        mock_api.search.return_value = SearchResult(
            query="related", total_results=5, papers=sample_papers
        )

        result = await server.find_related_papers("2401.00001", max_results=3)

        assert "original_paper" in result
        assert "related_papers" in result
        assert result["total_found"] <= 3

    async def test_original_not_found(self, server, mock_api):
        mock_api.get_paper.return_value = None

        result = await server.find_related_papers("bad_id")

        assert result["error"] == "Could not find original paper"

    async def test_exception(self, server, mock_api):
        mock_api.get_paper.side_effect = RuntimeError("fail")
        result = await server.find_related_papers("2401.00001")
        assert "error" in result


# ---------------------------------------------------------------------------
# get_paper_citations
# ---------------------------------------------------------------------------


class TestGetPaperCitations:

    async def test_success(self, server, mock_api, sample_paper):
        random.seed(42)
        mock_api.get_paper.return_value = sample_paper

        result = await server.get_paper_citations("2401.00001")

        assert result["arxiv_id"] == "2401.00001"
        assert "estimated_citations" in result
        assert "citations_per_year" in result
        assert "note" in result

    async def test_not_found(self, server, mock_api):
        mock_api.get_paper.return_value = None

        result = await server.get_paper_citations("bad_id")
        assert result == {"error": "Paper not found"}

    async def test_exception(self, server, mock_api):
        mock_api.get_paper.side_effect = RuntimeError("fail")
        result = await server.get_paper_citations("2401.00001")
        assert "error" in result


# ---------------------------------------------------------------------------
# analyze_trends
# ---------------------------------------------------------------------------


class TestAnalyzeTrends:

    async def test_success(self, server, mock_api, sample_papers):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=5, papers=sample_papers
        )

        result = await server.analyze_trends(
            category="cs.AI",
            time_period="3_months",
            analysis_type="publication_count",
        )

        assert result["category"] == "cs.AI"
        assert result["total_papers"] == 5
        assert "monthly_counts" in result

    async def test_exception(self, server, mock_api):
        mock_api.search.side_effect = RuntimeError("fail")

        result = await server.analyze_trends(category="cs.AI")
        # The TrendAnalyzer catches the exception and returns error in TrendAnalysis
        assert result.get("error") is not None or "error" in result


# ---------------------------------------------------------------------------
# export_papers
# ---------------------------------------------------------------------------


class TestExportPapers:

    async def test_bibtex(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.export_papers(
            ["2401.00001", "2401.00002"], format="bibtex"
        )

        assert "@article" in result

    async def test_json_format(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.export_papers(
            ["2401.00001", "2401.00002"], format="json"
        )

        import json
        parsed = json.loads(result)
        assert len(parsed) == 2

    async def test_csv_format(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.export_papers(
            ["2401.00001", "2401.00002"], format="csv"
        )

        assert "id" in result  # CSV header
        assert "2401.00001" in result

    async def test_markdown_format(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.export_papers(
            ["2401.00001", "2401.00002"], format="markdown"
        )

        assert "# arXiv Papers Export" in result

    async def test_no_valid_papers(self, server, mock_api):
        mock_api.get_paper.return_value = None

        result = await server.export_papers(["bad1"])
        assert "Error" in result

    async def test_include_abstract_false(self, server, mock_api, two_papers):
        mock_api.get_paper.side_effect = two_papers

        result = await server.export_papers(
            ["2401.00001", "2401.00002"],
            format="json",
            include_abstract=False,
        )

        import json
        parsed = json.loads(result)
        # abstract should be removed from JSON export
        assert "abstract" not in parsed[0]

    async def test_exception(self, server, mock_api):
        mock_api.get_paper.side_effect = RuntimeError("fail")
        result = await server.export_papers(["2401.00001"])
        assert "Error" in result


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:

    async def test_close_calls_api_close(self, server, mock_api):
        await server.close()
        mock_api.close.assert_awaited_once()
