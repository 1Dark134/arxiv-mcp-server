"""Tests for arxiv_mcp.exporters module."""

import csv
import json
from io import StringIO

import pytest

from arxiv_mcp.exporters import PaperExporter
from arxiv_mcp.models import ExportConfig, Paper


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def paper_with_special_chars():
    """Paper with characters that need escaping in BibTeX."""
    return Paper(
        id="2401.00099",
        title="Exploring {Quantum} Effects in {ML}",
        authors=["O'Brien, Pat", "van der Berg, Jan"],
        abstract="An abstract with {curly braces} and special chars.",
        published="2024-03-10",
        categories=["quant-ph", "cs.AI"],
        arxiv_url="https://arxiv.org/abs/2401.00099",
        pdf_url="https://arxiv.org/pdf/2401.00099",
    )


@pytest.fixture
def paper_empty_fields():
    """Paper with empty/minimal fields."""
    return Paper(
        id="",
        title="",
        authors=[],
        abstract="",
        published="",
        categories=[],
        arxiv_url="",
        pdf_url="",
    )


@pytest.fixture
def config_all_on():
    """ExportConfig with all options enabled."""
    return ExportConfig(
        format="bibtex",
        include_abstract=True,
        include_categories=True,
        include_urls=True,
    )


@pytest.fixture
def config_all_off():
    """ExportConfig with all optional fields disabled."""
    return ExportConfig(
        format="bibtex",
        include_abstract=False,
        include_categories=False,
        include_urls=False,
    )


# ---------------------------------------------------------------------------
# Unsupported format
# ---------------------------------------------------------------------------

class TestUnsupportedFormat:
    def test_raises_on_unknown_format(self, sample_paper):
        config = ExportConfig(format="xml")
        with pytest.raises(ValueError, match="Unsupported format"):
            PaperExporter.export_papers([sample_paper], config)

    def test_raises_on_empty_format(self, sample_paper):
        config = ExportConfig(format="")
        with pytest.raises(ValueError):
            PaperExporter.export_papers([sample_paper], config)


# ---------------------------------------------------------------------------
# BibTeX export
# ---------------------------------------------------------------------------

class TestBibtexExport:
    def test_basic_bibtex(self, sample_paper, config_all_on):
        config_all_on.format = "bibtex"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        assert "@article{" in result
        assert "Test Paper on Machine Learning" in result
        assert "Alice Smith and Bob Jones" in result
        assert "2024" in result
        assert "arXiv preprint" in result

    def test_bibtex_id_formatting(self, sample_paper, config_all_off):
        config_all_off.format = "bibtex"
        result = PaperExporter.export_papers([sample_paper], config_all_off)
        # dots and slashes should be replaced with underscores
        assert "2401_00001" in result

    def test_bibtex_with_urls(self, sample_paper):
        config = ExportConfig(format="bibtex", include_urls=True, include_abstract=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "url={https://export.arxiv.org/abs/" in result

    def test_bibtex_without_urls(self, sample_paper):
        config = ExportConfig(format="bibtex", include_urls=False, include_abstract=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "url=" not in result

    def test_bibtex_with_abstract(self, sample_paper):
        config = ExportConfig(format="bibtex", include_abstract=True, include_urls=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "abstract={" in result
        assert "novel approach to testing" in result

    def test_bibtex_without_abstract(self, sample_paper):
        config = ExportConfig(format="bibtex", include_abstract=False, include_urls=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "abstract=" not in result

    def test_bibtex_with_categories(self, sample_paper):
        config = ExportConfig(format="bibtex", include_categories=True, include_urls=False, include_abstract=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "note={Categories:" in result
        assert "cs.AI" in result

    def test_bibtex_without_categories(self, sample_paper):
        config = ExportConfig(format="bibtex", include_categories=False, include_urls=False, include_abstract=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "note=" not in result

    def test_bibtex_special_chars_escaped(self, paper_with_special_chars, config_all_on):
        config_all_on.format = "bibtex"
        result = PaperExporter.export_papers([paper_with_special_chars], config_all_on)
        # curly braces in title and abstract should be escaped
        assert "\\{Quantum\\}" in result
        assert "\\{curly braces\\}" in result

    def test_bibtex_multiple_papers(self, sample_papers, config_all_off):
        config_all_off.format = "bibtex"
        result = PaperExporter.export_papers(sample_papers, config_all_off)
        # entries separated by double newlines
        assert result.count("@article{") == len(sample_papers)

    def test_bibtex_empty_list(self, config_all_on):
        config_all_on.format = "bibtex"
        result = PaperExporter.export_papers([], config_all_on)
        assert result == ""

    def test_bibtex_empty_published(self, paper_empty_fields, config_all_off):
        config_all_off.format = "bibtex"
        result = PaperExporter.export_papers([paper_empty_fields], config_all_off)
        assert "year={}" in result

    def test_bibtex_no_categories_skips_note(self, paper_empty_fields):
        config = ExportConfig(format="bibtex", include_categories=True)
        result = PaperExporter.export_papers([paper_empty_fields], config)
        # empty categories list should skip the note field
        assert "note=" not in result


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

class TestJsonExport:
    def test_basic_json(self, sample_paper, config_all_on):
        config_all_on.format = "json"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "2401.00001"
        assert data[0]["title"] == "Test Paper on Machine Learning"

    def test_json_includes_all_fields_by_default(self, sample_paper, config_all_on):
        config_all_on.format = "json"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        data = json.loads(result)
        paper = data[0]
        assert "abstract" in paper
        assert "categories" in paper
        assert "arxiv_url" in paper
        assert "pdf_url" in paper

    def test_json_excludes_abstract(self, sample_paper):
        config = ExportConfig(format="json", include_abstract=False)
        result = PaperExporter.export_papers([sample_paper], config)
        data = json.loads(result)
        assert "abstract" not in data[0]

    def test_json_excludes_categories(self, sample_paper):
        config = ExportConfig(format="json", include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        data = json.loads(result)
        assert "categories" not in data[0]

    def test_json_excludes_urls(self, sample_paper):
        config = ExportConfig(format="json", include_urls=False)
        result = PaperExporter.export_papers([sample_paper], config)
        data = json.loads(result)
        assert "arxiv_url" not in data[0]
        assert "pdf_url" not in data[0]

    def test_json_excludes_all_optional(self, sample_paper, config_all_off):
        config_all_off.format = "json"
        result = PaperExporter.export_papers([sample_paper], config_all_off)
        data = json.loads(result)
        paper = data[0]
        assert "abstract" not in paper
        assert "categories" not in paper
        assert "arxiv_url" not in paper
        assert "pdf_url" not in paper
        # core fields remain
        assert "id" in paper
        assert "title" in paper
        assert "authors" in paper
        assert "published" in paper

    def test_json_multiple_papers(self, sample_papers, config_all_on):
        config_all_on.format = "json"
        result = PaperExporter.export_papers(sample_papers, config_all_on)
        data = json.loads(result)
        assert len(data) == len(sample_papers)

    def test_json_empty_list(self, config_all_on):
        config_all_on.format = "json"
        result = PaperExporter.export_papers([], config_all_on)
        data = json.loads(result)
        assert data == []

    def test_json_paper_with_empty_fields(self, paper_empty_fields, config_all_on):
        config_all_on.format = "json"
        result = PaperExporter.export_papers([paper_empty_fields], config_all_on)
        data = json.loads(result)
        assert data[0]["id"] == ""
        assert data[0]["authors"] == []

    def test_json_is_valid_and_indented(self, sample_paper, config_all_on):
        config_all_on.format = "json"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        # should be pretty-printed with 2-space indent
        assert "\n" in result
        assert "  " in result


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

class TestCsvExport:
    def _parse_csv(self, csv_string):
        reader = csv.DictReader(StringIO(csv_string))
        return list(reader), reader.fieldnames

    def test_basic_csv(self, sample_paper, config_all_on):
        config_all_on.format = "csv"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        rows, fieldnames = self._parse_csv(result)
        assert len(rows) == 1
        assert rows[0]["id"] == "2401.00001"
        assert rows[0]["title"] == "Test Paper on Machine Learning"

    def test_csv_core_fieldnames(self, sample_paper, config_all_off):
        config_all_off.format = "csv"
        result = PaperExporter.export_papers([sample_paper], config_all_off)
        _, fieldnames = self._parse_csv(result)
        assert "id" in fieldnames
        assert "title" in fieldnames
        assert "authors" in fieldnames
        assert "published" in fieldnames
        # optional fields excluded
        assert "abstract" not in fieldnames
        assert "categories" not in fieldnames
        assert "arxiv_url" not in fieldnames
        assert "pdf_url" not in fieldnames

    def test_csv_with_all_fields(self, sample_paper, config_all_on):
        config_all_on.format = "csv"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        _, fieldnames = self._parse_csv(result)
        assert "abstract" in fieldnames
        assert "categories" in fieldnames
        assert "arxiv_url" in fieldnames
        assert "pdf_url" in fieldnames

    def test_csv_authors_semicolon_separated(self, sample_paper, config_all_off):
        config_all_off.format = "csv"
        result = PaperExporter.export_papers([sample_paper], config_all_off)
        rows, _ = self._parse_csv(result)
        assert rows[0]["authors"] == "Alice Smith; Bob Jones"

    def test_csv_categories_semicolon_separated(self, sample_paper):
        config = ExportConfig(format="csv", include_categories=True, include_abstract=False, include_urls=False)
        result = PaperExporter.export_papers([sample_paper], config)
        rows, _ = self._parse_csv(result)
        assert rows[0]["categories"] == "cs.AI; cs.LG"

    def test_csv_multiple_papers(self, sample_papers, config_all_off):
        config_all_off.format = "csv"
        result = PaperExporter.export_papers(sample_papers, config_all_off)
        rows, _ = self._parse_csv(result)
        assert len(rows) == len(sample_papers)

    def test_csv_empty_list(self, config_all_off):
        config_all_off.format = "csv"
        result = PaperExporter.export_papers([], config_all_off)
        rows, _ = self._parse_csv(result)
        assert len(rows) == 0

    def test_csv_paper_with_empty_authors(self, paper_empty_fields, config_all_off):
        config_all_off.format = "csv"
        result = PaperExporter.export_papers([paper_empty_fields], config_all_off)
        rows, _ = self._parse_csv(result)
        assert rows[0]["authors"] == ""

    def test_csv_field_order(self, sample_paper):
        config = ExportConfig(format="csv", include_categories=True, include_urls=True, include_abstract=True)
        result = PaperExporter.export_papers([sample_paper], config)
        _, fieldnames = self._parse_csv(result)
        # field order: id, title, authors, published, categories, arxiv_url, pdf_url, abstract
        assert fieldnames.index("categories") < fieldnames.index("arxiv_url")
        assert fieldnames.index("arxiv_url") < fieldnames.index("abstract")


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

class TestMarkdownExport:
    def test_basic_markdown(self, sample_paper, config_all_on):
        config_all_on.format = "markdown"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        assert "# arXiv Papers Export" in result
        assert "## 1. Test Paper on Machine Learning" in result
        assert "Alice Smith, Bob Jones" in result
        assert "2401.00001" in result

    def test_markdown_includes_published(self, sample_paper, config_all_off):
        config_all_off.format = "markdown"
        result = PaperExporter.export_papers([sample_paper], config_all_off)
        assert "**Published:** 2024-01-01" in result

    def test_markdown_with_categories(self, sample_paper):
        config = ExportConfig(format="markdown", include_categories=True, include_urls=False, include_abstract=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "**Categories:** cs.AI, cs.LG" in result

    def test_markdown_without_categories(self, sample_paper):
        config = ExportConfig(format="markdown", include_categories=False, include_urls=False, include_abstract=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "**Categories:**" not in result

    def test_markdown_with_urls(self, sample_paper):
        config = ExportConfig(format="markdown", include_urls=True, include_abstract=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "**PDF:** [Download]" in result

    def test_markdown_without_urls(self, sample_paper):
        config = ExportConfig(format="markdown", include_urls=False, include_abstract=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "**PDF:**" not in result

    def test_markdown_with_abstract(self, sample_paper):
        config = ExportConfig(format="markdown", include_abstract=True, include_urls=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "**Abstract:**" in result
        assert "novel approach to testing" in result

    def test_markdown_without_abstract(self, sample_paper):
        config = ExportConfig(format="markdown", include_abstract=False, include_urls=False, include_categories=False)
        result = PaperExporter.export_papers([sample_paper], config)
        assert "**Abstract:**" not in result

    def test_markdown_numbering(self, sample_papers, config_all_off):
        config_all_off.format = "markdown"
        result = PaperExporter.export_papers(sample_papers, config_all_off)
        assert "## 1." in result
        assert "## 2." in result
        assert f"## {len(sample_papers)}." in result

    def test_markdown_separator(self, sample_papers, config_all_off):
        config_all_off.format = "markdown"
        result = PaperExporter.export_papers(sample_papers, config_all_off)
        assert result.count("---") == len(sample_papers)

    def test_markdown_empty_list(self, config_all_on):
        config_all_on.format = "markdown"
        result = PaperExporter.export_papers([], config_all_on)
        assert "# arXiv Papers Export" in result
        assert "##" not in result.replace("# arXiv Papers Export", "")

    def test_markdown_empty_categories_skips(self, paper_empty_fields):
        config = ExportConfig(format="markdown", include_categories=True)
        result = PaperExporter.export_papers([paper_empty_fields], config)
        # empty categories list should skip the categories line
        assert "**Categories:**" not in result

    def test_markdown_all_options_on(self, sample_paper, config_all_on):
        config_all_on.format = "markdown"
        result = PaperExporter.export_papers([sample_paper], config_all_on)
        assert "**Categories:**" in result
        assert "**PDF:**" in result
        assert "**Abstract:**" in result


# ---------------------------------------------------------------------------
# Default ExportConfig (from conftest fixture)
# ---------------------------------------------------------------------------

class TestDefaultExportConfig:
    def test_default_config_values(self, sample_export_config):
        assert sample_export_config.format == "bibtex"
        assert sample_export_config.include_abstract is True
        assert sample_export_config.include_categories is True
        assert sample_export_config.include_urls is True

    def test_default_config_produces_bibtex(self, sample_paper, sample_export_config):
        result = PaperExporter.export_papers([sample_paper], sample_export_config)
        assert "@article{" in result
