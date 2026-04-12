"""Tests for arxiv_mcp.client module."""

import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from arxiv_mcp.client import ArxivMCPClient
from arxiv_mcp.exceptions import ArxivConnectionError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Fresh ArxivMCPClient (not connected)."""
    return ArxivMCPClient()


@pytest.fixture
def mock_session():
    """A mock ClientSession with common response helpers."""
    session = AsyncMock()
    return session


@pytest.fixture
def connected_client(client, mock_session):
    """An ArxivMCPClient with a mock session already attached."""
    client.session = mock_session
    return client


def _tool_response(content_text: str):
    """Build a mock tool response with TextContent."""
    content = MagicMock()
    content.text = content_text
    response = MagicMock()
    response.content = [content]
    return response


def _empty_response():
    """Build a mock tool response with no content."""
    response = MagicMock()
    response.content = []
    return response


# We need to patch CallToolRequest because the installed MCP version
# requires a `params` wrapper that the client code doesn't provide.
# This is a known incompatibility in the source; we test the logic, not
# the MCP pydantic schema.
@pytest.fixture(autouse=True)
def patch_call_tool_request():
    """Replace CallToolRequest with a simple namespace so client methods don't
    hit pydantic validation errors from a newer MCP SDK."""
    class FakeCallToolRequest:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    with patch("arxiv_mcp.client.CallToolRequest", FakeCallToolRequest):
        yield


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------


class TestClientConnection:

    def test_initial_state(self, client):
        assert client.session is None
        assert client.http_client is not None
        assert client.base_url.startswith("https://")

    @patch("arxiv_mcp.client.stdio_client", new_callable=AsyncMock)
    @patch("arxiv_mcp.client.ClientSession")
    async def test_connect_success(self, MockSession, mock_stdio, client):
        mock_transport = (MagicMock(), MagicMock())
        # stdio_client is an async context manager, but the client code
        # calls it with `await` (a known source-level issue). We mock it
        # as an AsyncMock so `await stdio_client(...)` resolves to the
        # transport tuple.
        mock_stdio.return_value = mock_transport

        session_instance = AsyncMock()
        MockSession.return_value = session_instance

        await client.connect("server.py")

        mock_stdio.assert_called_once()
        MockSession.assert_called_once_with(mock_transport[0], mock_transport[1])
        session_instance.initialize.assert_awaited_once()
        assert client.session is session_instance

    async def test_close_with_session(self, connected_client):
        await connected_client.close()
        connected_client.session.close.assert_awaited_once()

    async def test_close_without_session(self, client):
        """Close should not raise even if session is None."""
        await client.close()  # should not raise


# ---------------------------------------------------------------------------
# Disconnected state - all methods should raise RuntimeError
# ---------------------------------------------------------------------------


class TestDisconnectedErrors:

    async def test_list_tools_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.list_tools()

    async def test_search_papers_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.search_papers("query")

    async def test_get_paper_details_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.get_paper_details("2401.00001")

    async def test_get_paper_summary_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.get_paper_summary("2401.00001")

    async def test_search_by_author_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.search_by_author("Smith")

    async def test_search_by_category_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.search_by_category("cs.AI")

    async def test_get_recent_papers_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.get_recent_papers()

    async def test_compare_papers_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.compare_papers(["id1", "id2"])

    async def test_find_related_papers_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.find_related_papers("2401.00001")

    async def test_export_papers_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.export_papers(["2401.00001"])

    async def test_list_resources_disconnected(self, client):
        with pytest.raises(ArxivConnectionError, match="Not connected"):
            await client.list_resources()


# ---------------------------------------------------------------------------
# Tool calls - JSON-returning methods
# ---------------------------------------------------------------------------


class TestSearchPapers:

    async def test_search_papers_returns_parsed_json(self, connected_client, mock_session):
        payload = {"papers": [{"id": "2401.00001"}], "total": 1}
        mock_session.call_tool.return_value = _tool_response(json.dumps(payload))

        result = await connected_client.search_papers("machine learning", max_results=5)

        assert result == payload
        mock_session.call_tool.assert_awaited_once()

    async def test_search_papers_empty_response(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _empty_response()

        result = await connected_client.search_papers("query")
        assert result == {}


class TestGetPaperDetails:

    async def test_returns_parsed_json(self, connected_client, mock_session):
        payload = {"id": "2401.00001", "title": "Test"}
        mock_session.call_tool.return_value = _tool_response(json.dumps(payload))

        result = await connected_client.get_paper_details("2401.00001")
        assert result == payload

    async def test_empty_response(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _empty_response()
        result = await connected_client.get_paper_details("2401.00001")
        assert result == {}


class TestGetPaperSummary:

    async def test_returns_text(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _tool_response("# Summary\nGreat paper.")

        result = await connected_client.get_paper_summary("2401.00001")
        assert "Summary" in result

    async def test_empty_response(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _empty_response()
        result = await connected_client.get_paper_summary("2401.00001")
        assert result == ""


class TestSearchByAuthor:

    async def test_returns_parsed_json(self, connected_client, mock_session):
        payload = {"papers": []}
        mock_session.call_tool.return_value = _tool_response(json.dumps(payload))

        result = await connected_client.search_by_author("Hinton", max_results=5)
        assert result == payload

    async def test_empty_response(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _empty_response()
        result = await connected_client.search_by_author("Hinton")
        assert result == {}


class TestSearchByCategory:

    async def test_returns_parsed_json(self, connected_client, mock_session):
        payload = {"papers": [], "total": 0}
        mock_session.call_tool.return_value = _tool_response(json.dumps(payload))

        result = await connected_client.search_by_category("cs.AI", max_results=10, sort_by="submittedDate")
        assert result == payload


class TestGetRecentPapers:

    async def test_returns_parsed_json(self, connected_client, mock_session):
        payload = {"papers": [{"id": "2401.00001"}]}
        mock_session.call_tool.return_value = _tool_response(json.dumps(payload))

        result = await connected_client.get_recent_papers(category="cs.AI", days_back=3, max_results=5)
        assert result == payload


class TestComparePapers:

    async def test_returns_text(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _tool_response("# Comparison\n...")

        result = await connected_client.compare_papers(["id1", "id2"])
        assert "Comparison" in result

    async def test_custom_fields(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _tool_response("result")

        result = await connected_client.compare_papers(
            ["id1", "id2"], comparison_fields=["authors"]
        )
        assert result == "result"

    async def test_default_comparison_fields(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _tool_response("result")

        await connected_client.compare_papers(["id1", "id2"])
        # Verify session.call_tool was called with a request that has the right arguments
        call_args = mock_session.call_tool.call_args[0][0]
        assert call_args.arguments["comparison_fields"] == [
            "authors", "categories", "abstract", "published"
        ]

    async def test_empty_response(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _empty_response()
        result = await connected_client.compare_papers(["id1", "id2"])
        assert result == ""


class TestFindRelatedPapers:

    async def test_returns_parsed_json(self, connected_client, mock_session):
        payload = {"related_papers": []}
        mock_session.call_tool.return_value = _tool_response(json.dumps(payload))

        result = await connected_client.find_related_papers("2401.00001", max_results=5)
        assert result == payload


class TestExportPapers:

    async def test_returns_text(self, connected_client, mock_session):
        bibtex = "@article{test, title={Test}}"
        mock_session.call_tool.return_value = _tool_response(bibtex)

        result = await connected_client.export_papers(
            ["2401.00001"], format="bibtex", include_abstract=False
        )
        assert "@article" in result

    async def test_empty_response(self, connected_client, mock_session):
        mock_session.call_tool.return_value = _empty_response()
        result = await connected_client.export_papers(["2401.00001"])
        assert result == ""


class TestListTools:

    async def test_returns_tools(self, connected_client, mock_session):
        tool = MagicMock()
        tool.name = "search_arxiv"
        resp = MagicMock()
        resp.tools = [tool]
        mock_session.list_tools.return_value = resp

        tools = await connected_client.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "search_arxiv"


class TestListResources:

    async def test_returns_resources(self, connected_client, mock_session):
        resource = MagicMock()
        resource.name = "papers"
        resp = MagicMock()
        resp.resources = [resource]
        mock_session.list_resources.return_value = resp

        resources = await connected_client.list_resources()
        assert len(resources) == 1
