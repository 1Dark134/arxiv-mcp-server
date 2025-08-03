import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

from .models import Paper, CitationInfo, TrendAnalysis
from .api import ArxivAPI

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze research trends and patterns."""

    def __init__(self, api_client: ArxivAPI):
        self.api = api_client

    async def analyze_trends(
            self,
            category: str,
            time_period: str = "3_months",
            analysis_type: str = "publication_count"
    ) -> TrendAnalysis:
        """Analyze publication trends in a specific field."""
        try:
            # Calculate time period
            period_days = {
                "1_month": 30,
                "3_months": 90,
                "6_months": 180,
                "1_year": 365
            }

            days = period_days.get(time_period, 90)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Build query for time range
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            query = f"cat:{category} AND submittedDate:[{start_str} TO {end_str}]"

            # Get papers from the time period
            results = await self.api.search(query, max_results=100, sort_by="submittedDate")

            if results.error:
                return TrendAnalysis(
                    category=category,
                    time_period=time_period,
                    analysis_type=analysis_type,
                    total_papers=0,
                    data={},
                    error=results.error
                )

            # Perform analysis based on type
            if analysis_type == "publication_count":
                data = self._analyze_publication_count(results.papers)
            elif analysis_type == "top_authors":
                data = self._analyze_top_authors(results.papers)
            elif analysis_type == "keyword_frequency":
                data = self._analyze_keyword_frequency(results.papers)
            else:
                data = {}

            return TrendAnalysis(
                category=category,
                time_period=time_period,
                analysis_type=analysis_type,
                total_papers=len(results.papers),
                data=data
            )

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return TrendAnalysis(
                category=category,
                time_period=time_period,
                analysis_type=analysis_type,
                total_papers=0,
                data={},
                error=str(e)
            )

    def _analyze_publication_count(self, papers: List[Paper]) -> Dict[str, Any]:
        """Count papers by month."""
        monthly_counts = {}
        for paper in papers:
            if paper.published:
                month_key = paper.published[:7]  # YYYY-MM format
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

        return {"monthly_counts": dict(sorted(monthly_counts.items()))}

    def _analyze_top_authors(self, papers: List[Paper]) -> Dict[str, Any]:
        """Count papers by author."""
        author_counts = {}
        for paper in papers:
            for author in paper.authors:
                author_counts[author] = author_counts.get(author, 0) + 1

        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "top_authors": [
                {"author": author, "paper_count": count}
                for author, count in top_authors
            ]
        }

    def _analyze_keyword_frequency(self, papers: List[Paper]) -> Dict[str, Any]:
        """Analyze keyword frequency in titles."""
        all_words = []
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'via', 'using'
        }

        for paper in papers:
            title = paper.title.lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', title)  # Words with 4+ letters
            filtered_words = [word for word in words if word not in stop_words]
            all_words.extend(filtered_words)

        word_freq = Counter(all_words).most_common(20)
        return {
            "top_keywords": [
                {"keyword": word, "frequency": freq}
                for word, freq in word_freq
            ]
        }


class CitationAnalyzer:
    """Analyze citation patterns and metrics."""

    @staticmethod
    def estimate_citations(paper: Paper) -> CitationInfo:
        """Estimate citation metrics for a paper."""
        try:
            if not paper.published:
                return CitationInfo(
                    arxiv_id=paper.id,
                    title=paper.title,
                    estimated_citations=0,
                    citations_per_year=0.0,
                    h_index_contribution=0,
                    note="Could not determine publication date"
                )

            # Calculate paper age
            pub_year = int(paper.published[:4])
            current_year = datetime.now().year
            age_years = max(1, current_year - pub_year)

            # Simulate citation count based on age and category
            base_citations = max(0, (age_years * random.randint(5, 25)) - random.randint(0, 20))

            # Adjust for popular categories
            popular_categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL']
            if any(cat in popular_categories for cat in paper.categories):
                base_citations = int(base_citations * 1.5)

            citations_per_year = round(base_citations / age_years, 1)
            h_index_contribution = min(base_citations, 10)  # Simplified h-index

            return CitationInfo(
                arxiv_id=paper.id,
                title=paper.title,
                estimated_citations=base_citations,
                citations_per_year=citations_per_year,
                h_index_contribution=h_index_contribution,
                note="Citation data is estimated/simulated as arXiv doesn't track citations directly"
            )

        except Exception as e:
            logger.error(f"Error estimating citations for {paper.id}: {e}")
            return CitationInfo(
                arxiv_id=paper.id,
                title=paper.title,
                estimated_citations=0,
                citations_per_year=0.0,
                h_index_contribution=0,
                note=f"Error estimating citations: {str(e)}"
            )


class RelatedPaperFinder:
    """Find papers related to a given paper."""

    def __init__(self, api_client: ArxivAPI):
        self.api = api_client

    async def find_related_papers(
            self,
            paper: Paper,
            max_results: int = 10
    ) -> List[Paper]:
        """Find papers related to a given paper."""
        try:
            # Extract keywords from title and categories
            title_words = paper.title.lower().split()
            categories = paper.categories

            # Build search query using categories and key terms
            search_terms = []

            # Add category searches
            for cat in categories[:2]:  # Limit to first 2 categories
                search_terms.append(f"cat:{cat}")

            # Add important words from title
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                'to', 'for', 'of', 'with', 'by', 'via', 'using'
            }
            key_words = [
                            word for word in title_words
                            if len(word) > 3 and word not in stop_words
                        ][:3]

            for word in key_words:
                search_terms.append(f'"{word}"')

            # Combine search terms
            query = " OR ".join(search_terms) if search_terms else (
                categories[0] if categories else "cs.AI"
            )

            # Search for related papers
            results = await self.api.search(query, max_results + 5, "relevance")

            # Filter out the original paper
            related_papers = [
                                 p for p in results.papers
                                 if p.id != paper.id
                             ][:max_results]

            return related_papers

        except Exception as e:
            logger.error(f"Error finding related papers: {e}")
            return []