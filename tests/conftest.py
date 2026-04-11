"""Shared fixtures for arxiv-mcp-server tests."""

import pytest

from arxiv_mcp.models import Paper, SearchResult, CitationInfo, TrendAnalysis, ExportConfig


@pytest.fixture
def sample_paper():
    """A minimal Paper instance for tests."""
    return Paper(
        id="2401.00001",
        title="Test Paper on Machine Learning",
        authors=["Alice Smith", "Bob Jones"],
        abstract="This paper presents a novel approach to testing.",
        categories=["cs.AI", "cs.LG"],
        published="2024-01-01",
        arxiv_url="https://arxiv.org/abs/2401.00001",
        pdf_url="https://arxiv.org/pdf/2401.00001",
    )


@pytest.fixture
def sample_papers(sample_paper):
    """A list of Paper instances for batch-operation tests."""
    papers = [sample_paper]
    for i in range(2, 6):
        papers.append(
            Paper(
                id=f"2401.0000{i}",
                title=f"Test Paper {i}",
                authors=[f"Author {i}"],
                abstract=f"Abstract for paper {i}.",
                categories=["cs.AI"],
                published=f"2024-01-0{i}",
                arxiv_url=f"https://arxiv.org/abs/2401.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2401.0000{i}",
            )
        )
    return papers


@pytest.fixture
def sample_search_result(sample_papers):
    """A SearchResult wrapping sample papers."""
    return SearchResult(
        query="machine learning",
        total_results=len(sample_papers),
        papers=sample_papers,
    )


@pytest.fixture
def sample_citation_info():
    """A CitationInfo instance for tests."""
    return CitationInfo(
        arxiv_id="2401.00001",
        title="Test Paper on Machine Learning",
        estimated_citations=42,
        citations_per_year=10.5,
        h_index_contribution=3,
        note="Estimated based on metadata",
    )


@pytest.fixture
def sample_trend_analysis():
    """A TrendAnalysis instance for tests."""
    return TrendAnalysis(
        category="cs.AI",
        time_period="2024-01",
        analysis_type="keyword",
        total_papers=150,
        data={"top_keywords": ["transformer", "llm"], "growth_rate": 0.15},
    )


@pytest.fixture
def sample_export_config():
    """Default ExportConfig for tests."""
    return ExportConfig()
