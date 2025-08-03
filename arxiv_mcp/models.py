from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Paper:
    """Represents an arXiv paper."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    published: str
    categories: List[str]
    arxiv_url: str
    pdf_url: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """Create Paper from dictionary."""
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            authors=data.get('authors', []),
            abstract=data.get('abstract', ''),
            published=data.get('published', ''),
            categories=data.get('categories', []),
            arxiv_url=data.get('arxiv_url', ''),
            pdf_url=data.get('pdf_url', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Paper to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'published': self.published,
            'categories': self.categories,
            'arxiv_url': self.arxiv_url,
            'pdf_url': self.pdf_url
        }


@dataclass
class SearchResult:
    """Represents search results."""
    query: str
    total_results: int
    papers: List[Paper]
    error: Optional[str] = None


@dataclass
class CitationInfo:
    """Citation information for a paper."""
    arxiv_id: str
    title: str
    estimated_citations: int
    citations_per_year: float
    h_index_contribution: int
    note: str


@dataclass
class TrendAnalysis:
    """Research trend analysis results."""
    category: str
    time_period: str
    analysis_type: str
    total_papers: int
    data: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ExportConfig:
    """Configuration for paper export."""
    format: str = "bibtex"
    include_abstract: bool = True
    include_categories: bool = True
    include_urls: bool = True