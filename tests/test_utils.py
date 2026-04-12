"""Tests for arxiv_mcp.utils module."""

import logging
from datetime import datetime
from unittest.mock import patch

import pytest

from arxiv_mcp.models import Paper
from arxiv_mcp.utils import (
    SearchQueryBuilder,
    PaperComparator,
    PaperFormatter,
    setup_logging,
    validate_arxiv_id,
)


# ---------------------------------------------------------------------------
# SearchQueryBuilder
# ---------------------------------------------------------------------------

class TestSearchQueryBuilder:
    """Tests for SearchQueryBuilder static methods."""

    def test_build_author_query(self):
        assert SearchQueryBuilder.build_author_query("John Doe") == 'au:"John Doe"'

    def test_build_author_query_empty(self):
        assert SearchQueryBuilder.build_author_query("") == 'au:""'

    def test_build_category_query(self):
        assert SearchQueryBuilder.build_category_query("cs.AI") == "cat:cs.AI"

    def test_build_category_query_empty(self):
        assert SearchQueryBuilder.build_category_query("") == "cat:"

    def test_build_date_range_query_default_type(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 6, 30)
        result = SearchQueryBuilder.build_date_range_query(start, end)
        assert result == "submittedDate:[20240101 TO 20240630]"

    def test_build_date_range_query_custom_type(self):
        start = datetime(2023, 3, 15)
        end = datetime(2023, 4, 20)
        result = SearchQueryBuilder.build_date_range_query(
            start, end, date_type="lastUpdatedDate"
        )
        assert result == "lastUpdatedDate:[20230315 TO 20230420]"

    def test_build_date_range_same_day(self):
        d = datetime(2024, 5, 10)
        result = SearchQueryBuilder.build_date_range_query(d, d)
        assert result == "submittedDate:[20240510 TO 20240510]"

    def test_combine_queries_and(self):
        qs = ['au:"Smith"', "cat:cs.AI"]
        result = SearchQueryBuilder.combine_queries(qs)
        assert result == '(au:"Smith") AND (cat:cs.AI)'

    def test_combine_queries_or(self):
        qs = ["cat:cs.AI", "cat:cs.LG"]
        result = SearchQueryBuilder.combine_queries(qs, operator="OR")
        assert result == "(cat:cs.AI) OR (cat:cs.LG)"

    def test_combine_queries_single(self):
        result = SearchQueryBuilder.combine_queries(["cat:cs.AI"])
        assert result == "(cat:cs.AI)"

    def test_combine_queries_empty_list(self):
        result = SearchQueryBuilder.combine_queries([])
        assert result == ""


# ---------------------------------------------------------------------------
# PaperComparator
# ---------------------------------------------------------------------------

class TestPaperComparator:
    """Tests for PaperComparator."""

    def test_compare_no_papers(self):
        result = PaperComparator.compare_papers([], ["authors"])
        assert result == "No papers to compare"

    def test_compare_authors_field(self, sample_papers):
        result = PaperComparator.compare_papers(sample_papers[:2], ["authors"])
        assert "# Paper Comparison" in result
        assert "## Authors" in result
        assert "Paper 1" in result
        assert "Paper 2" in result
        # First paper has two authors, both shown
        assert "Alice Smith" in result

    def test_compare_categories_field(self, sample_paper):
        result = PaperComparator.compare_papers([sample_paper], ["categories"])
        assert "## Categories" in result
        assert "cs.AI" in result
        assert "cs.LG" in result

    def test_compare_abstract_field(self, sample_paper):
        result = PaperComparator.compare_papers([sample_paper], ["abstract"])
        assert "## Abstract" in result
        assert "novel approach" in result

    def test_compare_published_field(self, sample_paper):
        result = PaperComparator.compare_papers([sample_paper], ["published"])
        assert "## Published" in result
        assert "2024-01-01" in result

    def test_compare_long_title_truncated(self):
        """Titles longer than 60 chars get truncated with '...'."""
        paper = Paper(
            id="1234.56789",
            title="A" * 80,
            authors=["Author"],
            abstract="Abstract",
            published="2024-01-01",
            categories=["cs.AI"],
            arxiv_url="",
            pdf_url="",
        )
        result = PaperComparator.compare_papers([paper], ["authors"])
        assert "A" * 60 + "..." in result

    def test_compare_short_title_not_truncated(self, sample_paper):
        """Titles 60 chars or fewer are not truncated."""
        result = PaperComparator.compare_papers([sample_paper], ["authors"])
        assert sample_paper.title in result
        # Should NOT end with "..." for the title portion
        assert "..." not in sample_paper.title

    def test_compare_many_authors_truncated(self):
        """When a paper has >3 authors, only first 3 shown with '...'."""
        paper = Paper(
            id="1234.56789",
            title="Multi-Author Paper",
            authors=["A1", "A2", "A3", "A4", "A5"],
            abstract="",
            published="",
            categories=[],
            arxiv_url="",
            pdf_url="",
        )
        result = PaperComparator.compare_papers([paper], ["authors"])
        assert "A1, A2, A3..." in result
        assert "A4" not in result

    def test_compare_long_abstract_truncated(self):
        """Abstracts longer than 200 chars get truncated."""
        paper = Paper(
            id="1234.56789",
            title="Paper",
            authors=[],
            abstract="X" * 250,
            published="",
            categories=[],
            arxiv_url="",
            pdf_url="",
        )
        result = PaperComparator.compare_papers([paper], ["abstract"])
        assert "X" * 200 + "..." in result

    def test_compare_multiple_fields(self, sample_paper):
        """Multiple comparison fields produce multiple sections."""
        result = PaperComparator.compare_papers(
            [sample_paper], ["authors", "categories", "published"]
        )
        assert "## Authors" in result
        assert "## Categories" in result
        assert "## Published" in result

    def test_compare_unknown_field(self, sample_paper):
        """An unrecognized field still creates a section header but no detail lines."""
        result = PaperComparator.compare_papers([sample_paper], ["unknown_field"])
        assert "## Unknown_Field" in result


# ---------------------------------------------------------------------------
# PaperFormatter
# ---------------------------------------------------------------------------

class TestPaperFormatter:
    """Tests for PaperFormatter."""

    def test_format_paper_summary(self, sample_paper):
        summary = PaperFormatter.format_paper_summary(sample_paper)
        assert sample_paper.title in summary
        assert "Alice Smith" in summary
        assert "Bob Jones" in summary
        assert sample_paper.id in summary
        assert sample_paper.published in summary
        assert "cs.AI" in summary
        assert sample_paper.pdf_url in summary
        assert sample_paper.arxiv_url in summary
        assert "## Abstract" in summary

    def test_format_paper_summary_empty_authors(self):
        paper = Paper(
            id="0000.00000",
            title="No Authors",
            authors=[],
            abstract="",
            published="",
            categories=[],
            arxiv_url="",
            pdf_url="",
        )
        summary = PaperFormatter.format_paper_summary(paper)
        assert "**Authors:** \n" in summary

    def test_format_search_results_empty(self):
        result = PaperFormatter.format_search_results([])
        assert result == "No papers found."

    def test_format_search_results_basic(self, sample_papers):
        result = PaperFormatter.format_search_results(sample_papers)
        assert "Found 5 papers" in result
        assert "1. **Test Paper on Machine Learning**" in result

    def test_format_search_results_respects_max_display(self, sample_papers):
        """Only max_display papers shown, remainder noted."""
        result = PaperFormatter.format_search_results(sample_papers, max_display=2)
        assert "1. **" in result
        assert "2. **" in result
        # Papers 3-5 should not appear
        assert "3. **" not in result
        assert "... and 3 more papers." in result

    def test_format_search_results_max_display_exceeds_count(self, sample_papers):
        """When max_display >= paper count, no 'and X more' line."""
        result = PaperFormatter.format_search_results(sample_papers, max_display=100)
        assert "more papers" not in result

    def test_format_search_results_many_authors_truncated(self):
        """Authors list >3 is truncated in search results."""
        paper = Paper(
            id="0001.00001",
            title="Many Authors",
            authors=["A", "B", "C", "D"],
            abstract="",
            published="2024-01-01",
            categories=["cs.AI"],
            arxiv_url="",
            pdf_url="",
        )
        result = PaperFormatter.format_search_results([paper])
        assert "A, B, C..." in result

    def test_format_search_results_few_authors_not_truncated(self, sample_paper):
        """Authors list <=3 is not truncated."""
        result = PaperFormatter.format_search_results([sample_paper])
        # sample_paper has 2 authors, no trailing "..."
        assert "Alice Smith, Bob Jones\n" in result


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------

class TestSetupLogging:
    """Tests for setup_logging helper.

    pytest's logging plugin manages the root logger, so we mock
    logging.basicConfig to verify setup_logging passes the right args.
    """

    @patch("arxiv_mcp.utils.logging.basicConfig")
    def test_setup_logging_default(self, mock_basic):
        setup_logging()
        mock_basic.assert_called_once()
        kwargs = mock_basic.call_args
        assert kwargs[1]["level"] == logging.INFO

    @patch("arxiv_mcp.utils.logging.basicConfig")
    def test_setup_logging_debug(self, mock_basic):
        setup_logging("DEBUG")
        mock_basic.assert_called_once()
        assert mock_basic.call_args[1]["level"] == logging.DEBUG

    @patch("arxiv_mcp.utils.logging.basicConfig")
    def test_setup_logging_case_insensitive(self, mock_basic):
        setup_logging("warning")
        mock_basic.assert_called_once()
        assert mock_basic.call_args[1]["level"] == logging.WARNING

    @patch("arxiv_mcp.utils.logging.basicConfig")
    def test_setup_logging_format_string(self, mock_basic):
        setup_logging()
        fmt = mock_basic.call_args[1]["format"]
        assert "%(asctime)s" in fmt
        assert "%(levelname)s" in fmt


# ---------------------------------------------------------------------------
# validate_arxiv_id
# ---------------------------------------------------------------------------

class TestValidateArxivId:
    """Tests for validate_arxiv_id."""

    # Valid modern format
    @pytest.mark.parametrize("arxiv_id", [
        "2401.00001",
        "2401.12345",
        "9912.99999",
        "2401.0001",       # 4-digit paper number
        "2401.00001v1",    # versioned
        "2401.00001v12",   # multi-digit version
    ])
    def test_valid_modern_ids(self, arxiv_id):
        assert validate_arxiv_id(arxiv_id) is True

    # Valid old format
    @pytest.mark.parametrize("arxiv_id", [
        "hep-th/9901001",
        "math/0301001",
        "cond-mat/0001001",
        "math.AG/0301001",
    ])
    def test_valid_old_ids(self, arxiv_id):
        assert validate_arxiv_id(arxiv_id) is True

    # Invalid IDs
    @pytest.mark.parametrize("arxiv_id", [
        "",
        "not-an-id",
        "2401",
        "2401.",
        "2401.1",          # too few digits
        "2401.123456",     # 6-digit paper number
        "2401.00001v",     # v without number
        "ABCD.12345",      # letters in date part
        "hep-th/990100",   # old format too few digits
        "hep-th/99010010", # old format too many digits
        "HEP-TH/9901001",  # uppercase subject class
    ])
    def test_invalid_ids(self, arxiv_id):
        assert validate_arxiv_id(arxiv_id) is False
