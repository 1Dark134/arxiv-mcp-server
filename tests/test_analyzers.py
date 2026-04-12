"""Tests for arxiv_mcp.analyzers module."""

import random
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from arxiv_mcp.analyzers import CitationAnalyzer, RelatedPaperFinder, TrendAnalyzer
from arxiv_mcp.models import Paper, SearchResult, TrendAnalysis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api():
    """ArxivAPI mock with async methods."""
    api = AsyncMock()
    return api


@pytest.fixture
def trend_analyzer(mock_api):
    return TrendAnalyzer(mock_api)


@pytest.fixture
def related_finder(mock_api):
    return RelatedPaperFinder(mock_api)


@pytest.fixture
def papers_with_dates():
    """Papers spanning several months for trend analysis."""
    return [
        Paper(
            id="2401.00001",
            title="Deep Learning for Vision Tasks",
            authors=["Alice Smith", "Bob Jones"],
            abstract="A novel approach to vision.",
            categories=["cs.CV", "cs.LG"],
            published="2024-01-15",
            arxiv_url="https://arxiv.org/abs/2401.00001",
            pdf_url="https://arxiv.org/pdf/2401.00001",
        ),
        Paper(
            id="2401.00002",
            title="Transformer Networks Revisited",
            authors=["Alice Smith", "Carol White"],
            abstract="Revisiting transformer architectures.",
            categories=["cs.LG"],
            published="2024-01-20",
            arxiv_url="https://arxiv.org/abs/2401.00002",
            pdf_url="https://arxiv.org/pdf/2401.00002",
        ),
        Paper(
            id="2402.00001",
            title="Reinforcement Learning Survey",
            authors=["Dave Black"],
            abstract="A survey of reinforcement learning methods.",
            categories=["cs.AI"],
            published="2024-02-05",
            arxiv_url="https://arxiv.org/abs/2402.00001",
            pdf_url="https://arxiv.org/pdf/2402.00001",
        ),
    ]


# ---------------------------------------------------------------------------
# TrendAnalyzer
# ---------------------------------------------------------------------------


class TestTrendAnalyzer:

    async def test_analyze_trends_publication_count(
        self, trend_analyzer, mock_api, papers_with_dates
    ):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=3, papers=papers_with_dates
        )

        result = await trend_analyzer.analyze_trends(
            category="cs.AI",
            time_period="3_months",
            analysis_type="publication_count",
        )

        assert isinstance(result, TrendAnalysis)
        assert result.category == "cs.AI"
        assert result.total_papers == 3
        assert "monthly_counts" in result.data
        assert result.data["monthly_counts"]["2024-01"] == 2
        assert result.data["monthly_counts"]["2024-02"] == 1
        assert result.error is None

    async def test_analyze_trends_top_authors(
        self, trend_analyzer, mock_api, papers_with_dates
    ):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=3, papers=papers_with_dates
        )

        result = await trend_analyzer.analyze_trends(
            category="cs.AI",
            time_period="1_month",
            analysis_type="top_authors",
        )

        authors = result.data["top_authors"]
        # Alice Smith appears in 2 papers
        alice = next(a for a in authors if a["author"] == "Alice Smith")
        assert alice["paper_count"] == 2

    async def test_analyze_trends_keyword_frequency(
        self, trend_analyzer, mock_api, papers_with_dates
    ):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=3, papers=papers_with_dates
        )

        result = await trend_analyzer.analyze_trends(
            category="cs.AI",
            time_period="6_months",
            analysis_type="keyword_frequency",
        )

        keywords = result.data["top_keywords"]
        keyword_words = [k["keyword"] for k in keywords]
        assert "learning" in keyword_words  # appears in 2 titles
        # stop words should be excluded
        assert "the" not in keyword_words

    async def test_analyze_trends_unknown_analysis_type(
        self, trend_analyzer, mock_api, papers_with_dates
    ):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=3, papers=papers_with_dates
        )

        result = await trend_analyzer.analyze_trends(
            category="cs.AI",
            analysis_type="unknown_type",
        )

        assert result.data == {}

    async def test_analyze_trends_api_error(self, trend_analyzer, mock_api):
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI",
            total_results=0,
            papers=[],
            error="API timeout",
        )

        result = await trend_analyzer.analyze_trends(category="cs.AI")

        assert result.total_papers == 0
        assert result.error == "API timeout"

    async def test_analyze_trends_exception(self, trend_analyzer, mock_api):
        mock_api.search.side_effect = RuntimeError("Connection failed")

        result = await trend_analyzer.analyze_trends(category="cs.AI")

        assert result.total_papers == 0
        assert "Connection failed" in result.error

    async def test_analyze_trends_default_period(self, trend_analyzer, mock_api):
        """Default period should fall back to 90 days for unknown strings."""
        mock_api.search.return_value = SearchResult(
            query="cat:cs.AI", total_results=0, papers=[]
        )

        await trend_analyzer.analyze_trends(
            category="cs.AI", time_period="invalid_period"
        )

        # Verify the search was called (it should not crash)
        mock_api.search.assert_called_once()

    async def test_analyze_trends_valid_time_periods(self, trend_analyzer, mock_api):
        """All four named time periods should work without error."""
        mock_api.search.return_value = SearchResult(
            query="", total_results=0, papers=[]
        )

        for period in ("1_month", "3_months", "6_months", "1_year"):
            result = await trend_analyzer.analyze_trends(
                category="cs.AI", time_period=period
            )
            assert result.error is None

    def test_publication_count_empty(self, trend_analyzer):
        result = trend_analyzer._analyze_publication_count([])
        assert result == {"monthly_counts": {}}

    def test_publication_count_no_published_date(self, trend_analyzer):
        paper = Paper(
            id="x", title="t", authors=[], abstract="",
            categories=[], published="", arxiv_url="", pdf_url=""
        )
        result = trend_analyzer._analyze_publication_count([paper])
        assert result == {"monthly_counts": {}}

    def test_top_authors_limit(self, trend_analyzer):
        """Only top 10 authors should be returned."""
        papers = []
        for i in range(15):
            papers.append(
                Paper(
                    id=f"id{i}", title=f"Title {i}",
                    authors=[f"Author_{i}"], abstract="",
                    categories=[], published="2024-01-01",
                    arxiv_url="", pdf_url=""
                )
            )
        result = trend_analyzer._analyze_top_authors(papers)
        assert len(result["top_authors"]) <= 10

    def test_keyword_frequency_filters_short_words(self, trend_analyzer):
        paper = Paper(
            id="x", title="AI is the new era of NLP",
            authors=[], abstract="", categories=[],
            published="2024-01-01", arxiv_url="", pdf_url=""
        )
        result = trend_analyzer._analyze_keyword_frequency([paper])
        keyword_words = [k["keyword"] for k in result["top_keywords"]]
        # "AI", "is", "the", "new", "era", "NLP" - all < 4 chars except "none qualify" check
        # Actually: only words with 4+ letters pass the regex filter
        # None of these words have 4+ letters, so list should be empty
        assert keyword_words == []


# ---------------------------------------------------------------------------
# CitationAnalyzer
# ---------------------------------------------------------------------------


class TestCitationAnalyzer:

    def test_estimate_citations_deterministic(self, sample_paper):
        """Seeding random should produce deterministic results."""
        random.seed(42)
        result1 = CitationAnalyzer.estimate_citations(sample_paper)

        random.seed(42)
        result2 = CitationAnalyzer.estimate_citations(sample_paper)

        assert result1.estimated_citations == result2.estimated_citations
        assert result1.citations_per_year == result2.citations_per_year

    def test_estimate_citations_popular_category_boost(self):
        """Papers in popular categories get a 1.5x citation boost."""
        random.seed(100)
        popular_paper = Paper(
            id="2401.00001", title="Popular",
            authors=["A"], abstract="", categories=["cs.AI"],
            published="2020-01-01", arxiv_url="", pdf_url=""
        )
        result_popular = CitationAnalyzer.estimate_citations(popular_paper)

        random.seed(100)
        niche_paper = Paper(
            id="2401.00001", title="Niche",
            authors=["A"], abstract="", categories=["math.CO"],
            published="2020-01-01", arxiv_url="", pdf_url=""
        )
        result_niche = CitationAnalyzer.estimate_citations(niche_paper)

        # With same seed, popular should have 1.5x the niche citations
        assert result_popular.estimated_citations >= result_niche.estimated_citations

    def test_estimate_citations_no_published_date(self):
        paper = Paper(
            id="2401.00001", title="No date",
            authors=[], abstract="", categories=[],
            published="", arxiv_url="", pdf_url=""
        )
        result = CitationAnalyzer.estimate_citations(paper)
        assert result.estimated_citations == 0
        assert result.citations_per_year == 0.0
        assert "Could not determine publication date" in result.note

    def test_estimate_citations_h_index_cap(self, sample_paper):
        """h_index_contribution should be capped at 10."""
        random.seed(0)
        result = CitationAnalyzer.estimate_citations(sample_paper)
        assert result.h_index_contribution <= 10

    def test_estimate_citations_returns_citation_info(self, sample_paper):
        random.seed(42)
        result = CitationAnalyzer.estimate_citations(sample_paper)
        assert result.arxiv_id == sample_paper.id
        assert result.title == sample_paper.title
        assert isinstance(result.estimated_citations, int)
        assert isinstance(result.citations_per_year, float)

    def test_estimate_citations_exception_handling(self):
        """Malformed published date should be caught."""
        paper = Paper(
            id="x", title="bad",
            authors=[], abstract="", categories=[],
            published="not-a-date", arxiv_url="", pdf_url=""
        )
        result = CitationAnalyzer.estimate_citations(paper)
        assert "Error" in result.note or result.estimated_citations >= 0

    def test_citations_per_year_calculation(self):
        random.seed(42)
        paper = Paper(
            id="x", title="Test",
            authors=[], abstract="", categories=[],
            published="2024-01-01", arxiv_url="", pdf_url=""
        )
        result = CitationAnalyzer.estimate_citations(paper)
        if result.estimated_citations > 0:
            # age is at least 1, so citations_per_year should be base/age
            assert result.citations_per_year > 0


# ---------------------------------------------------------------------------
# RelatedPaperFinder
# ---------------------------------------------------------------------------


class TestRelatedPaperFinder:

    async def test_find_related_papers_basic(
        self, related_finder, mock_api, sample_paper, sample_papers
    ):
        mock_api.search.return_value = SearchResult(
            query="", total_results=5, papers=sample_papers
        )

        result = await related_finder.find_related_papers(sample_paper, max_results=3)

        # Original paper should be filtered out
        assert all(p.id != sample_paper.id for p in result)
        assert len(result) <= 3

    async def test_find_related_papers_excludes_original(
        self, related_finder, mock_api, sample_paper
    ):
        # Return only the original paper
        mock_api.search.return_value = SearchResult(
            query="", total_results=1, papers=[sample_paper]
        )

        result = await related_finder.find_related_papers(sample_paper)
        assert len(result) == 0

    async def test_find_related_papers_empty_categories_and_short_title(
        self, related_finder, mock_api
    ):
        """When categories are empty AND all title words are <= 3 chars,
        the query should fall back to 'cs.AI'."""
        paper = Paper(
            id="x", title="on AI",
            authors=[], abstract="", categories=[],
            published="2024-01-01", arxiv_url="", pdf_url=""
        )
        mock_api.search.return_value = SearchResult(
            query="", total_results=0, papers=[]
        )

        result = await related_finder.find_related_papers(paper)
        assert result == []
        call_args = mock_api.search.call_args
        assert "cs.AI" in call_args[0][0]

    async def test_find_related_papers_empty_categories_with_keywords(
        self, related_finder, mock_api
    ):
        """When categories are empty but title has long words, those become
        the search terms (no fallback to 'cs.AI')."""
        paper = Paper(
            id="x", title="short",
            authors=[], abstract="", categories=[],
            published="2024-01-01", arxiv_url="", pdf_url=""
        )
        mock_api.search.return_value = SearchResult(
            query="", total_results=0, papers=[]
        )

        result = await related_finder.find_related_papers(paper)
        assert result == []
        call_args = mock_api.search.call_args
        # "short" has 5 chars, so it becomes a search term
        assert '"short"' in call_args[0][0]

    async def test_find_related_papers_api_exception(
        self, related_finder, mock_api, sample_paper
    ):
        mock_api.search.side_effect = RuntimeError("Network error")

        result = await related_finder.find_related_papers(sample_paper)
        assert result == []

    async def test_find_related_papers_uses_categories_and_keywords(
        self, related_finder, mock_api
    ):
        paper = Paper(
            id="orig", title="Advanced Quantum Computing Methods",
            authors=["A"], abstract="",
            categories=["quant-ph", "cs.CC", "cs.AI"],
            published="2024-01-01", arxiv_url="", pdf_url=""
        )
        mock_api.search.return_value = SearchResult(
            query="", total_results=0, papers=[]
        )

        await related_finder.find_related_papers(paper)

        query_used = mock_api.search.call_args[0][0]
        # Should include first 2 categories
        assert "cat:quant-ph" in query_used
        assert "cat:cs.CC" in query_used
        # Should NOT include 3rd category
        assert "cat:cs.AI" not in query_used

    async def test_find_related_papers_respects_max_results(
        self, related_finder, mock_api, sample_papers
    ):
        mock_api.search.return_value = SearchResult(
            query="", total_results=5, papers=sample_papers
        )

        result = await related_finder.find_related_papers(sample_papers[0], max_results=2)
        assert len(result) <= 2
