"""MCP Server implementation for arXiv integration."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from mcp.types import Tool

from .api import ArxivAPI
from .models import Paper, ExportConfig
from .exporters import PaperExporter
from .analyzers import TrendAnalyzer, CitationAnalyzer, RelatedPaperFinder
from .utils import SearchQueryBuilder, PaperComparator, PaperFormatter

logger = logging.getLogger(__name__)


class ArxivMCPServer:
    """MCP Server for arXiv integration."""

    def __init__(self):
        self.api = ArxivAPI()
        self.trend_analyzer = TrendAnalyzer(self.api)
        self.citation_analyzer = CitationAnalyzer()
        self.related_finder = RelatedPaperFinder(self.api)

    def get_tools(self) -> List[Tool]:
        """Return available tools."""
        return [
            Tool(
                name="search_arxiv",
                description="Search for academic papers on arXiv",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (keywords, authors, titles, etc.)"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort results by relevance, lastUpdatedDate, or submittedDate",
                            "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                            "default": "relevance"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_paper",
                description="Get detailed information about a specific arXiv paper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "arXiv paper ID (e.g., '2301.07041' or 'cs.AI/0001001')"
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
            Tool(
                name="summarize_paper",
                description="Get a formatted summary of an arXiv paper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "arXiv paper ID"
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
            Tool(
                name="search_by_author",
                description="Search for papers by a specific author",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "author_name": {
                            "type": "string",
                            "description": "Author's name (e.g., 'Geoffrey Hinton', 'Yoshua Bengio')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["author_name"]
                }
            ),
            Tool(
                name="search_by_category",
                description="Search for papers in a specific arXiv category",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "arXiv category (e.g., 'cs.AI', 'cs.LG', 'math.CO', 'physics.gen-ph')",
                            "examples": ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "math.CO", "physics.gen-ph"]
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort results by lastUpdatedDate or submittedDate",
                            "enum": ["lastUpdatedDate", "submittedDate"],
                            "default": "submittedDate"
                        }
                    },
                    "required": ["category"]
                }
            ),
            Tool(
                name="get_recent_papers",
                description="Get the most recent papers from arXiv",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Optional category filter (e.g., 'cs.AI', 'cs.LG')",
                            "default": ""
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days back to search (default: 7)",
                            "default": 7,
                            "minimum": 1,
                            "maximum": 30
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 15,
                            "minimum": 1,
                            "maximum": 100
                        }
                    }
                }
            ),
            Tool(
                name="compare_papers",
                description="Compare multiple papers side by side",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of arXiv paper IDs to compare",
                            "minItems": 2,
                            "maxItems": 5
                        },
                        "comparison_fields": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["authors", "categories", "abstract", "published", "citations"]
                            },
                            "description": "Fields to compare (default: all)",
                            "default": ["authors", "categories", "abstract", "published"]
                        }
                    },
                    "required": ["arxiv_ids"]
                }
            ),
            Tool(
                name="find_related_papers",
                description="Find papers related to a given paper based on categories and keywords",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "arXiv paper ID to find related papers for"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of related papers to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
            Tool(
                name="get_paper_citations",
                description="Get citation information and metrics for a paper (simulated)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "arXiv paper ID"
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
            Tool(
                name="analyze_trends",
                description="Analyze publication trends in a specific field or category",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "arXiv category to analyze (e.g., 'cs.AI', 'cs.LG')"
                        },
                        "time_period": {
                            "type": "string",
                            "description": "Time period for analysis",
                            "enum": ["1_month", "3_months", "6_months", "1_year"],
                            "default": "3_months"
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "Type of trend analysis",
                            "enum": ["publication_count", "top_authors", "keyword_frequency"],
                            "default": "publication_count"
                        }
                    },
                    "required": ["category"]
                }
            ),
            Tool(
                name="export_papers",
                description="Export paper information in various formats",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of arXiv paper IDs to export"
                        },
                        "format": {
                            "type": "string",
                            "description": "Export format",
                            "enum": ["bibtex", "json", "csv", "markdown"],
                            "default": "bibtex"
                        },
                        "include_abstract": {
                            "type": "boolean",
                            "description": "Include abstracts in export",
                            "default": True
                        }
                    },
                    "required": ["arxiv_ids"]
                }
            )
        ]

    async def search_arxiv(
            self,
            query: str,
            max_results: int = 10,
            sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """Search arXiv for papers."""
        try:
            results = await self.api.search(query, max_results, sort_by)

            return {
                "query": query,
                "total_results": results.total_results,
                "papers": [paper.to_dict() for paper in results.papers],
                "error": results.error
            }

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return {"error": str(e), "papers": []}

    async def get_paper(self, arxiv_id: str) -> Dict[str, Any]:
        """Get details for a specific paper."""
        try:
            paper = await self.api.get_paper(arxiv_id)

            if paper:
                return paper.to_dict()
            else:
                return {"error": "Paper not found"}

        except Exception as e:
            logger.error(f"Error getting paper {arxiv_id}: {e}")
            return {"error": str(e)}

    async def summarize_paper(self, arxiv_id: str) -> str:
        """Get a formatted summary of a paper."""
        try:
            paper = await self.api.get_paper(arxiv_id)

            if paper:
                return PaperFormatter.format_paper_summary(paper)
            else:
                return "Error: Paper not found"

        except Exception as e:
            logger.error(f"Error summarizing paper {arxiv_id}: {e}")
            return f"Error: {str(e)}"

    async def search_by_author(
            self,
            author_name: str,
            max_results: int = 20
    ) -> Dict[str, Any]:
        """Search for papers by a specific author."""
        try:
            query = SearchQueryBuilder.build_author_query(author_name)
            return await self.search_arxiv(query, max_results, "submittedDate")

        except Exception as e:
            logger.error(f"Error searching by author {author_name}: {e}")
            return {"error": str(e), "papers": []}

    async def search_by_category(
            self,
            category: str,
            max_results: int = 20,
            sort_by: str = "submittedDate"
    ) -> Dict[str, Any]:
        """Search for papers in a specific category."""
        try:
            query = SearchQueryBuilder.build_category_query(category)
            return await self.search_arxiv(query, max_results, sort_by)

        except Exception as e:
            logger.error(f"Error searching category {category}: {e}")
            return {"error": str(e), "papers": []}

    async def get_recent_papers(
            self,
            category: str = "",
            days_back: int = 7,
            max_results: int = 15
    ) -> Dict[str, Any]:
        """Get recent papers from the last N days."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Build query
            date_query = SearchQueryBuilder.build_date_range_query(start_date, end_date)

            if category:
                category_query = SearchQueryBuilder.build_category_query(category)
                query = SearchQueryBuilder.combine_queries([category_query, date_query])
            else:
                query = date_query

            return await self.search_arxiv(query, max_results, "submittedDate")

        except Exception as e:
            logger.error(f"Error getting recent papers: {e}")
            return {"error": str(e), "papers": []}

    async def compare_papers(
            self,
            arxiv_ids: List[str],
            comparison_fields: List[str] = None
    ) -> str:
        """Compare multiple papers side by side."""
        if comparison_fields is None:
            comparison_fields = ["authors", "categories", "abstract", "published"]

        try:
            papers = []
            for arxiv_id in arxiv_ids:
                paper = await self.api.get_paper(arxiv_id)
                if paper:
                    papers.append(paper)

            if not papers:
                return "Error: No valid papers found for comparison"

            return PaperComparator.compare_papers(papers, comparison_fields)

        except Exception as e:
            logger.error(f"Error comparing papers: {e}")
            return f"Error comparing papers: {str(e)}"

    async def find_related_papers(
            self,
            arxiv_id: str,
            max_results: int = 10
    ) -> Dict[str, Any]:
        """Find papers related to a given paper."""
        try:
            # Get the original paper
            original_paper = await self.api.get_paper(arxiv_id)
            if not original_paper:
                return {"error": "Could not find original paper", "papers": []}

            # Find related papers
            related_papers = await self.related_finder.find_related_papers(
                original_paper, max_results
            )

            return {
                "original_paper": original_paper.to_dict(),
                "related_papers": [paper.to_dict() for paper in related_papers],
                "total_found": len(related_papers)
            }

        except Exception as e:
            logger.error(f"Error finding related papers: {e}")
            return {"error": str(e), "papers": []}

    async def get_paper_citations(self, arxiv_id: str) -> Dict[str, Any]:
        """Get citation information for a paper."""
        try:
            paper = await self.api.get_paper(arxiv_id)
            if not paper:
                return {"error": "Paper not found"}

            citation_info = self.citation_analyzer.estimate_citations(paper)

            return {
                "arxiv_id": citation_info.arxiv_id,
                "title": citation_info.title,
                "estimated_citations": citation_info.estimated_citations,
                "citations_per_year": citation_info.citations_per_year,
                "h_index_contribution": citation_info.h_index_contribution,
                "note": citation_info.note
            }

        except Exception as e:
            logger.error(f"Error getting citations for {arxiv_id}: {e}")
            return {"error": str(e)}

    async def analyze_trends(
            self,
            category: str,
            time_period: str = "3_months",
            analysis_type: str = "publication_count"
    ) -> Dict[str, Any]:
        """Analyze publication trends in a specific field."""
        try:
            analysis = await self.trend_analyzer.analyze_trends(
                category, time_period, analysis_type
            )

            return {
                "category": analysis.category,
                "time_period": analysis.time_period,
                "analysis_type": analysis.analysis_type,
                "total_papers": analysis.total_papers,
                **analysis.data,
                "error": analysis.error
            }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"error": str(e)}

    async def export_papers(
            self,
            arxiv_ids: List[str],
            format: str = "bibtex",
            include_abstract: bool = True
    ) -> str:
        """Export papers in various formats."""
        try:
            papers = []
            for arxiv_id in arxiv_ids:
                paper = await self.api.get_paper(arxiv_id)
                if paper:
                    papers.append(paper)

            if not papers:
                return "Error: No valid papers found for export"

            config = ExportConfig(
                format=format,
                include_abstract=include_abstract
            )

            return PaperExporter.export_papers(papers, config)

        except Exception as e:
            logger.error(f"Error exporting papers: {e}")
            return f"Error exporting papers: {str(e)}"

    async def close(self):
        """Close the server and cleanup resources."""
        await self.api.close()