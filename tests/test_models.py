"""Tests for arxiv_mcp.models module."""

import pytest

from arxiv_mcp.models import Paper, SearchResult, CitationInfo, TrendAnalysis, ExportConfig


class TestPaper:
    """Tests for the Paper dataclass."""

    def test_paper_creation(self, sample_paper):
        """Paper can be created with all required fields."""
        assert sample_paper.id == "2401.00001"
        assert sample_paper.title == "Test Paper on Machine Learning"
        assert sample_paper.authors == ["Alice Smith", "Bob Jones"]
        assert sample_paper.abstract == "This paper presents a novel approach to testing."
        assert sample_paper.published == "2024-01-01"
        assert sample_paper.categories == ["cs.AI", "cs.LG"]
        assert sample_paper.arxiv_url == "https://arxiv.org/abs/2401.00001"
        assert sample_paper.pdf_url == "https://arxiv.org/pdf/2401.00001"

    def test_paper_from_dict_full(self):
        """from_dict creates a Paper from a complete dictionary."""
        data = {
            "id": "2401.99999",
            "title": "Full Dict Paper",
            "authors": ["Author A"],
            "abstract": "Some abstract.",
            "published": "2024-01-15",
            "categories": ["cs.CL"],
            "arxiv_url": "https://arxiv.org/abs/2401.99999",
            "pdf_url": "https://arxiv.org/pdf/2401.99999",
        }
        paper = Paper.from_dict(data)
        assert paper.id == "2401.99999"
        assert paper.title == "Full Dict Paper"
        assert paper.authors == ["Author A"]
        assert paper.abstract == "Some abstract."
        assert paper.published == "2024-01-15"
        assert paper.categories == ["cs.CL"]
        assert paper.arxiv_url == "https://arxiv.org/abs/2401.99999"
        assert paper.pdf_url == "https://arxiv.org/pdf/2401.99999"

    def test_paper_from_dict_empty(self):
        """from_dict with an empty dict uses defaults for every field."""
        paper = Paper.from_dict({})
        assert paper.id == ""
        assert paper.title == ""
        assert paper.authors == []
        assert paper.abstract == ""
        assert paper.published == ""
        assert paper.categories == []
        assert paper.arxiv_url == ""
        assert paper.pdf_url == ""

    def test_paper_from_dict_missing_keys(self):
        """from_dict fills in defaults for any missing keys."""
        data = {"id": "2401.00001", "title": "Partial Paper"}
        paper = Paper.from_dict(data)
        assert paper.id == "2401.00001"
        assert paper.title == "Partial Paper"
        assert paper.authors == []
        assert paper.abstract == ""
        assert paper.published == ""
        assert paper.categories == []
        assert paper.arxiv_url == ""
        assert paper.pdf_url == ""

    def test_paper_from_dict_extra_keys_ignored(self):
        """from_dict ignores keys not in the dataclass."""
        data = {
            "id": "2401.00001",
            "title": "Paper",
            "authors": [],
            "abstract": "",
            "published": "",
            "categories": [],
            "arxiv_url": "",
            "pdf_url": "",
            "extra_field": "should be ignored",
        }
        paper = Paper.from_dict(data)
        assert paper.id == "2401.00001"
        assert not hasattr(paper, "extra_field")

    def test_paper_from_dict_empty_strings(self):
        """from_dict handles explicitly empty string values."""
        data = {
            "id": "",
            "title": "",
            "authors": [],
            "abstract": "",
            "published": "",
            "categories": [],
            "arxiv_url": "",
            "pdf_url": "",
        }
        paper = Paper.from_dict(data)
        assert paper.id == ""
        assert paper.title == ""

    def test_paper_to_dict(self, sample_paper):
        """to_dict returns a dictionary with all paper fields."""
        d = sample_paper.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == "2401.00001"
        assert d["title"] == "Test Paper on Machine Learning"
        assert d["authors"] == ["Alice Smith", "Bob Jones"]
        assert d["abstract"] == "This paper presents a novel approach to testing."
        assert d["published"] == "2024-01-01"
        assert d["categories"] == ["cs.AI", "cs.LG"]
        assert d["arxiv_url"] == "https://arxiv.org/abs/2401.00001"
        assert d["pdf_url"] == "https://arxiv.org/pdf/2401.00001"

    def test_paper_roundtrip(self, sample_paper):
        """Converting to dict and back produces an equal Paper."""
        d = sample_paper.to_dict()
        restored = Paper.from_dict(d)
        assert restored == sample_paper

    def test_paper_to_dict_has_correct_keys(self, sample_paper):
        """to_dict contains exactly the expected keys."""
        expected_keys = {
            "id", "title", "authors", "abstract",
            "published", "categories", "arxiv_url", "pdf_url",
        }
        assert set(sample_paper.to_dict().keys()) == expected_keys

    def test_paper_equality(self):
        """Two Papers with identical fields are equal (dataclass default)."""
        p1 = Paper(
            id="1", title="T", authors=[], abstract="",
            published="", categories=[], arxiv_url="", pdf_url="",
        )
        p2 = Paper(
            id="1", title="T", authors=[], abstract="",
            published="", categories=[], arxiv_url="", pdf_url="",
        )
        assert p1 == p2

    def test_paper_inequality(self):
        """Papers with different fields are not equal."""
        p1 = Paper(
            id="1", title="T1", authors=[], abstract="",
            published="", categories=[], arxiv_url="", pdf_url="",
        )
        p2 = Paper(
            id="2", title="T2", authors=[], abstract="",
            published="", categories=[], arxiv_url="", pdf_url="",
        )
        assert p1 != p2


class TestSearchResult:
    """Tests for the SearchResult dataclass."""

    def test_search_result_creation(self, sample_search_result):
        """SearchResult holds query, count, papers, and optional error."""
        assert sample_search_result.query == "machine learning"
        assert sample_search_result.total_results == 5
        assert len(sample_search_result.papers) == 5
        assert sample_search_result.error is None

    def test_search_result_with_error(self):
        """SearchResult can carry an error string."""
        sr = SearchResult(
            query="bad query",
            total_results=0,
            papers=[],
            error="API timeout",
        )
        assert sr.error == "API timeout"
        assert sr.total_results == 0
        assert sr.papers == []

    def test_search_result_default_error_is_none(self):
        """error defaults to None when not provided."""
        sr = SearchResult(query="q", total_results=0, papers=[])
        assert sr.error is None

    def test_search_result_empty_papers(self):
        """SearchResult with zero papers and zero total_results."""
        sr = SearchResult(query="nothing", total_results=0, papers=[])
        assert sr.total_results == 0
        assert sr.papers == []


class TestCitationInfo:
    """Tests for the CitationInfo dataclass."""

    def test_citation_info_creation(self, sample_citation_info):
        """CitationInfo stores citation metrics."""
        assert sample_citation_info.arxiv_id == "2401.00001"
        assert sample_citation_info.title == "Test Paper on Machine Learning"
        assert sample_citation_info.estimated_citations == 42
        assert sample_citation_info.citations_per_year == 10.5
        assert sample_citation_info.h_index_contribution == 3
        assert sample_citation_info.note == "Estimated based on metadata"

    def test_citation_info_zero_citations(self):
        """CitationInfo with zero values."""
        ci = CitationInfo(
            arxiv_id="0000.00000",
            title="Uncited Paper",
            estimated_citations=0,
            citations_per_year=0.0,
            h_index_contribution=0,
            note="",
        )
        assert ci.estimated_citations == 0
        assert ci.citations_per_year == 0.0
        assert ci.h_index_contribution == 0
        assert ci.note == ""


class TestTrendAnalysis:
    """Tests for the TrendAnalysis dataclass."""

    def test_trend_analysis_creation(self, sample_trend_analysis):
        """TrendAnalysis stores trend data and metadata."""
        assert sample_trend_analysis.category == "cs.AI"
        assert sample_trend_analysis.time_period == "2024-01"
        assert sample_trend_analysis.analysis_type == "keyword"
        assert sample_trend_analysis.total_papers == 150
        assert sample_trend_analysis.data == {
            "top_keywords": ["transformer", "llm"],
            "growth_rate": 0.15,
        }
        assert sample_trend_analysis.error is None

    def test_trend_analysis_with_error(self):
        """TrendAnalysis can carry an error."""
        ta = TrendAnalysis(
            category="cs.AI",
            time_period="2024-01",
            analysis_type="keyword",
            total_papers=0,
            data={},
            error="No data available",
        )
        assert ta.error == "No data available"
        assert ta.data == {}

    def test_trend_analysis_default_error_is_none(self):
        """error defaults to None."""
        ta = TrendAnalysis(
            category="cs.AI",
            time_period="2024-01",
            analysis_type="keyword",
            total_papers=0,
            data={},
        )
        assert ta.error is None

    def test_trend_analysis_complex_data(self):
        """TrendAnalysis data can hold nested structures."""
        nested = {
            "clusters": [{"name": "A", "count": 10}, {"name": "B", "count": 5}],
            "metadata": {"source": "test"},
        }
        ta = TrendAnalysis(
            category="cs.CL",
            time_period="2024-Q1",
            analysis_type="clustering",
            total_papers=15,
            data=nested,
        )
        assert len(ta.data["clusters"]) == 2


class TestExportConfig:
    """Tests for the ExportConfig dataclass."""

    def test_export_config_defaults(self, sample_export_config):
        """ExportConfig has sensible defaults."""
        assert sample_export_config.format == "bibtex"
        assert sample_export_config.include_abstract is True
        assert sample_export_config.include_categories is True
        assert sample_export_config.include_urls is True

    def test_export_config_custom_values(self):
        """ExportConfig accepts custom values."""
        ec = ExportConfig(
            format="json",
            include_abstract=False,
            include_categories=False,
            include_urls=False,
        )
        assert ec.format == "json"
        assert ec.include_abstract is False
        assert ec.include_categories is False
        assert ec.include_urls is False

    def test_export_config_partial_override(self):
        """ExportConfig allows overriding only some defaults."""
        ec = ExportConfig(format="csv")
        assert ec.format == "csv"
        assert ec.include_abstract is True  # default kept
