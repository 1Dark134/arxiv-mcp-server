import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus

import httpx

from .models import Paper, SearchResult

logger = logging.getLogger(__name__)


class ArxivAPI:
    """arXiv API client."""

    def __init__(self, timeout: float = 30.0):
        self.http_client = httpx.AsyncClient(timeout=timeout)
        self.base_url = "https://export.arxiv.org/api/query" #"http://export.arxiv.org/api/query"

    async def search(
            self,
            query: str,
            max_results: int = 10,
            sort_by: str = "relevance"
    ) -> SearchResult:
        """Search arXiv for papers."""
        try:
            encoded_query = quote_plus(query)
            sort_order = "descending" if sort_by != "relevance" else "ascending"

            url = f"{self.base_url}?search_query={encoded_query}&start=0&max_results={max_results}&sortBy={sort_by}&sortOrder={sort_order}"

            response = await self.http_client.get(url)
            response.raise_for_status()

            papers = self._parse_response(response.content)

            return SearchResult(
                query=query,
                total_results=len(papers),
                papers=papers
            )

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return SearchResult(
                query=query,
                total_results=0,
                papers=[],
                error=str(e)
            )

    async def get_paper(self, arxiv_id: str) -> Optional[Paper]:
        """Get details for a specific paper."""
        try:
            clean_id = arxiv_id.replace("arXiv:", "").replace("v1", "").replace("v2", "").replace("v3", "")

            url = f"{self.base_url}?id_list={clean_id}"
            response = await self.http_client.get(url)
            response.raise_for_status()

            papers = self._parse_response(response.content)
            return papers[0] if papers else None

        except Exception as e:
            logger.error(f"Error getting paper {arxiv_id}: {e}")
            return None

    def _parse_response(self, content: bytes) -> List[Paper]:
        """Parse arXiv XML response into Paper objects."""
        try:
            root = ET.fromstring(content)
            papers = []

            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                paper_data = self._parse_paper_entry(entry)
                if paper_data:
                    papers.append(Paper.from_dict(paper_data))

            return papers

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return []

    def _parse_paper_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Parse an arXiv entry XML element into a paper dictionary."""
        try:
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'https://export.arxiv.org/schemas/atom'}

            # Extract basic information
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else "Unknown Title"

            # Extract authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Extract abstract
            summary_elem = entry.find('atom:summary', ns)
            abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else ""

            # Extract arXiv ID
            id_elem = entry.find('atom:id', ns)
            arxiv_url = id_elem.text if id_elem is not None else ""
            arxiv_id = arxiv_url.split('/')[-1] if arxiv_url else ""

            # Extract publication date
            published_elem = entry.find('atom:published', ns)
            published = published_elem.text[:10] if published_elem is not None else ""

            # Extract categories
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)

            # Find PDF link
            pdf_url = ""
            for link in entry.findall('atom:link', ns):
                if link.get('type') == 'application/pdf':
                    pdf_url = link.get('href', '')
                    break

            return {
                "id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "published": published,
                "categories": categories,
                "arxiv_url": arxiv_url,
                "pdf_url": pdf_url
            }

        except Exception as e:
            logger.error(f"Error parsing paper entry: {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()