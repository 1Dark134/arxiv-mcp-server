import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import (
    CallToolRequest,
    GetPromptRequest,
    ListPromptsRequest,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
    Resource,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArxivMCPClient:
    """MCP Client for interacting with arXiv API"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://export.arxiv.org/api/query" #"http://export.arxiv.org/api/query"

    async def connect(self, server_script_path: str):
        """Connect to the MCP server"""
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )

        stdio_transport = await stdio_client(server_params)
        self.session = ClientSession(stdio_transport[0], stdio_transport[1])

        # Initialize the session
        await self.session.initialize()
        logger.info("Connected to arXiv MCP server")

    async def list_tools(self) -> List[Tool]:
        """List available tools from the MCP server"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        response = await self.session.list_tools(ListToolsRequest())
        return response.tools

    async def search_papers(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search for papers on arXiv"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="search_arxiv",
            arguments={
                "query": query,
                "max_results": max_results
            }
        )

        response = await self.session.call_tool(request)
        return json.loads(response.content[0].text) if response.content else {}

    async def get_paper_details(self, arxiv_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific paper"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="get_paper",
            arguments={"arxiv_id": arxiv_id}
        )

        response = await self.session.call_tool(request)
        return json.loads(response.content[0].text) if response.content else {}

    async def get_paper_summary(self, arxiv_id: str) -> str:
        """Get a formatted summary of a paper"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="summarize_paper",
            arguments={"arxiv_id": arxiv_id}
        )

        response = await self.session.call_tool(request)
        return response.content[0].text if response.content else ""

    async def search_by_author(self, author_name: str, max_results: int = 20) -> Dict[str, Any]:
        """Search for papers by a specific author"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="search_by_author",
            arguments={"author_name": author_name, "max_results": max_results}
        )

        response = await self.session.call_tool(request)
        return json.loads(response.content[0].text) if response.content else {}

    async def search_by_category(self, category: str, max_results: int = 20, sort_by: str = "submittedDate") -> Dict[str, Any]:
        """Search for papers in a specific category"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="search_by_category",
            arguments={"category": category, "max_results": max_results, "sort_by": sort_by}
        )

        response = await self.session.call_tool(request)
        return json.loads(response.content[0].text) if response.content else {}

    async def get_recent_papers(self, category: str = "", days_back: int = 7, max_results: int = 15) -> Dict[str, Any]:
        """Get recent papers"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="get_recent_papers",
            arguments={"category": category, "days_back": days_back, "max_results": max_results}
        )

        response = await self.session.call_tool(request)
        return json.loads(response.content[0].text) if response.content else {}

    async def compare_papers(self, arxiv_ids: List[str], comparison_fields: List[str] = None) -> str:
        """Compare multiple papers"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        if comparison_fields is None:
            comparison_fields = ["authors", "categories", "abstract", "published"]

        request = CallToolRequest(
            name="compare_papers",
            arguments={"arxiv_ids": arxiv_ids, "comparison_fields": comparison_fields}
        )

        response = await self.session.call_tool(request)
        return response.content[0].text if response.content else ""

    async def find_related_papers(self, arxiv_id: str, max_results: int = 10) -> Dict[str, Any]:
        """Find papers related to a given paper"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="find_related_papers",
            arguments={"arxiv_id": arxiv_id, "max_results": max_results}
        )

        response = await self.session.call_tool(request)
        return json.loads(response.content[0].text) if response.content else {}

    async def export_papers(self, arxiv_ids: List[str], format: str = "bibtex", include_abstract: bool = True) -> str:
        """Export papers in various formats"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        request = CallToolRequest(
            name="export_papers",
            arguments={"arxiv_ids": arxiv_ids, "format": format, "include_abstract": include_abstract}
        )

        response = await self.session.call_tool(request)
        return response.content[0].text if response.content else ""

    async def list_resources(self) -> List[Resource]:
        """List available resources"""
        if not self.session:
            raise RuntimeError("Not connected to server")

        response = await self.session.list_resources(ListResourcesRequest())
        return response.resources

    async def close(self):
        """Close the connection"""
        if self.http_client:
            await self.http_client.aclose()
        if self.session:
            await self.session.close()
