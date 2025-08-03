import logging
from typing import List, Dict, Any
from datetime import datetime

from .models import Paper

logger = logging.getLogger(__name__)


class SearchQueryBuilder:
    """Build complex search queries for arXiv API."""

    @staticmethod
    def build_author_query(author_name: str) -> str:
        """Build query to search by author."""
        return f'au:"{author_name}"'

    @staticmethod
    def build_category_query(category: str) -> str:
        """Build query to search by category."""
        return f"cat:{category}"

    @staticmethod
    def build_date_range_query(
            start_date: datetime,
            end_date: datetime,
            date_type: str = "submittedDate"
    ) -> str:
        """Build query with date range."""
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        return f"{date_type}:[{start_str} TO {end_str}]"

    @staticmethod
    def combine_queries(queries: List[str], operator: str = "AND") -> str:
        """Combine multiple queries with AND/OR operator."""
        return f" {operator} ".join(f"({q})" for q in queries)


class PaperComparator:
    """Compare papers and generate comparison reports."""

    @staticmethod
    def compare_papers(
            papers: List[Paper],
            comparison_fields: List[str]
    ) -> str:
        """Generate a comparison report for multiple papers."""
        if not papers:
            return "No papers to compare"

        comparison = "# Paper Comparison\n\n"

        for field in comparison_fields:
            comparison += f"## {field.title()}\n\n"

            for i, paper in enumerate(papers, 1):
                title_preview = paper.title[:60] + "..." if len(paper.title) > 60 else paper.title
                comparison += f"**Paper {i}** ({paper.id}): {title_preview}\n"

                if field == "authors":
                    authors = ", ".join(paper.authors[:3])
                    if len(paper.authors) > 3:
                        authors += "..."
                    comparison += f"- Authors: {authors}\n\n"

                elif field == "categories":
                    categories = ", ".join(paper.categories)
                    comparison += f"- Categories: {categories}\n\n"

                elif field == "abstract":
                    abstract = paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract
                    comparison += f"- Abstract: {abstract}\n\n"

                elif field == "published":
                    comparison += f"- Published: {paper.published}\n\n"

            comparison += "\n---\n\n"

        return comparison


class PaperFormatter:
    """Format papers for display and summaries."""

    @staticmethod
    def format_paper_summary(paper: Paper) -> str:
        """Generate a formatted summary of a paper."""
        summary = f"# {paper.title}\n\n"
        summary += f"**Authors:** {', '.join(paper.authors)}\n"
        summary += f"**Published:** {paper.published}\n"
        summary += f"**arXiv ID:** {paper.id}\n"
        summary += f"**Categories:** {', '.join(paper.categories)}\n\n"
        summary += f"## Abstract\n{paper.abstract}\n\n"
        summary += f"**PDF:** {paper.pdf_url}\n"
        summary += f"**arXiv Page:** {paper.arxiv_url}\n"
        return summary

    @staticmethod
    def format_search_results(papers: List[Paper], max_display: int = 10) -> str:
        """Format search results for display."""
        if not papers:
            return "No papers found."

        result = f"Found {len(papers)} papers:\n\n"

        for i, paper in enumerate(papers[:max_display], 1):
            result += f"{i}. **{paper.title}**\n"
            result += f"   Authors: {', '.join(paper.authors[:3])}"
            if len(paper.authors) > 3:
                result += "..."
            result += f"\n   arXiv ID: {paper.id}\n"
            result += f"   Published: {paper.published}\n"
            result += f"   Categories: {', '.join(paper.categories)}\n\n"

        if len(papers) > max_display:
            result += f"... and {len(papers) - max_display} more papers.\n"

        return result


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_arxiv_id(arxiv_id: str) -> bool:
    """Validate arXiv ID format."""
    import re

    # Modern format: YYMM.NNNNN[vN]
    modern_pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'

    # Old format: subject-class/YYMMnnn
    old_pattern = r'^[a-z-]+(\.[A-Z]{2})?/\d{7}$'

    return bool(re.match(modern_pattern, arxiv_id) or re.match(old_pattern, arxiv_id))