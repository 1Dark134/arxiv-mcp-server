"""Tests for arxiv_mcp.api module."""

import pytest
import httpx
import respx

from arxiv_mcp.api import ArxivAPI
from arxiv_mcp.models import Paper, SearchResult


# ---------------------------------------------------------------------------
# Helpers: sample XML responses
# ---------------------------------------------------------------------------

SAMPLE_ENTRY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="https://export.arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2401.00001v1</id>
    <title>Test Paper on Machine Learning</title>
    <summary>This paper presents a novel approach.</summary>
    <published>2024-01-15T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <category term="cs.AI"/>
    <category term="cs.LG"/>
    <link href="https://arxiv.org/pdf/2401.00001v1" type="application/pdf"/>
  </entry>
</feed>"""

MULTI_ENTRY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="https://export.arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2401.00001v1</id>
    <title>Paper One</title>
    <summary>Abstract one.</summary>
    <published>2024-01-01T00:00:00Z</published>
    <author><name>Author A</name></author>
    <category term="cs.AI"/>
    <link href="https://arxiv.org/pdf/2401.00001v1" type="application/pdf"/>
  </entry>
  <entry>
    <id>https://arxiv.org/abs/2401.00002v1</id>
    <title>Paper Two</title>
    <summary>Abstract two.</summary>
    <published>2024-01-02T00:00:00Z</published>
    <author><name>Author B</name></author>
    <category term="cs.CL"/>
  </entry>
</feed>"""

EMPTY_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""

MALFORMED_XML = b"this is not xml at all <<<<>>>"

ENTRY_MISSING_FIELDS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="https://export.arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2401.99999v1</id>
  </entry>
</feed>"""

ENTRY_MULTILINE_TITLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="https://export.arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2401.00001v1</id>
    <title>
      A Very Long Title That
      Spans Multiple Lines
    </title>
    <summary>Short abstract.</summary>
    <published>2024-06-01T00:00:00Z</published>
    <author><name>Charlie</name></author>
    <category term="math.CO"/>
  </entry>
</feed>"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api():
    return ArxivAPI(timeout=5.0)


@pytest.fixture
async def api_cleanup(api):
    """Yield the API client and close it after the test."""
    yield api
    await api.close()


# ---------------------------------------------------------------------------
# ArxivAPI.__init__
# ---------------------------------------------------------------------------

class TestArxivAPIInit:
    def test_default_timeout(self):
        client = ArxivAPI()
        assert client.http_client.timeout.connect == 30.0

    def test_custom_timeout(self):
        client = ArxivAPI(timeout=10.0)
        assert client.http_client.timeout.connect == 10.0

    def test_base_url(self):
        client = ArxivAPI()
        assert "export.arxiv.org" in client.base_url


# ---------------------------------------------------------------------------
# ArxivAPI.search
# ---------------------------------------------------------------------------

class TestSearch:
    @respx.mock
    async def test_search_success_single_result(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=SAMPLE_ENTRY_XML.encode())
        )
        result = await api.search("machine learning", max_results=1)
        assert isinstance(result, SearchResult)
        assert result.query == "machine learning"
        assert result.total_results == 1
        assert result.error is None
        paper = result.papers[0]
        assert paper.id == "2401.00001v1"
        assert paper.title == "Test Paper on Machine Learning"
        assert paper.authors == ["Alice Smith", "Bob Jones"]
        assert paper.abstract == "This paper presents a novel approach."
        assert paper.published == "2024-01-15"
        assert paper.categories == ["cs.AI", "cs.LG"]
        assert "pdf" in paper.pdf_url

    @respx.mock
    async def test_search_success_multiple_results(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=MULTI_ENTRY_XML.encode())
        )
        result = await api.search("deep learning", max_results=10)
        assert result.total_results == 2
        assert len(result.papers) == 2
        assert result.papers[0].title == "Paper One"
        assert result.papers[1].title == "Paper Two"

    @respx.mock
    async def test_search_empty_results(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=EMPTY_FEED_XML.encode())
        )
        result = await api.search("nonexistent topic xyz")
        assert result.total_results == 0
        assert result.papers == []
        assert result.error is None

    @respx.mock
    async def test_search_http_error(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(500, content=b"Internal Server Error")
        )
        result = await api.search("test query")
        assert result.total_results == 0
        assert result.papers == []
        assert result.error is not None

    @respx.mock
    async def test_search_network_error(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(side_effect=httpx.ConnectError("Connection refused"))
        result = await api.search("test query")
        assert result.total_results == 0
        assert result.error is not None
        assert result.query == "test query"

    @respx.mock
    async def test_search_timeout(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(side_effect=httpx.ReadTimeout("Timed out"))
        result = await api.search("slow query")
        assert result.total_results == 0
        assert result.error is not None

    @respx.mock
    async def test_search_malformed_xml(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=MALFORMED_XML)
        )
        result = await api.search("broken response")
        assert result.total_results == 0
        assert result.papers == []
        # malformed XML is caught in _parse_response; search returns empty list, no error field
        assert result.error is None

    @respx.mock
    async def test_search_sort_by_relevance(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=EMPTY_FEED_XML.encode())
        )
        await api.search("test", sort_by="relevance")
        request = route.calls[0].request
        assert "sortBy=relevance" in str(request.url)
        assert "sortOrder=ascending" in str(request.url)

    @respx.mock
    async def test_search_sort_by_date(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=EMPTY_FEED_XML.encode())
        )
        await api.search("test", sort_by="submittedDate")
        request = route.calls[0].request
        assert "sortBy=submittedDate" in str(request.url)
        assert "sortOrder=descending" in str(request.url)

    @respx.mock
    async def test_search_query_encoding(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=EMPTY_FEED_XML.encode())
        )
        await api.search("quantum computing + physics")
        request = route.calls[0].request
        url_str = str(request.url)
        # spaces and + should be encoded
        assert "quantum" in url_str

    @respx.mock
    async def test_search_max_results_in_url(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=EMPTY_FEED_XML.encode())
        )
        await api.search("test", max_results=25)
        request = route.calls[0].request
        assert "max_results=25" in str(request.url)


# ---------------------------------------------------------------------------
# ArxivAPI.get_paper
# ---------------------------------------------------------------------------

class TestGetPaper:
    @respx.mock
    async def test_get_paper_success(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=SAMPLE_ENTRY_XML.encode())
        )
        paper = await api.get_paper("2401.00001")
        assert paper is not None
        assert isinstance(paper, Paper)
        assert paper.title == "Test Paper on Machine Learning"

    @respx.mock
    async def test_get_paper_with_arxiv_prefix(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=SAMPLE_ENTRY_XML.encode())
        )
        paper = await api.get_paper("arXiv:2401.00001")
        request = route.calls[0].request
        # arXiv: prefix should be stripped
        assert "arXiv%3A" not in str(request.url)
        assert paper is not None

    @respx.mock
    async def test_get_paper_strips_version(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=SAMPLE_ENTRY_XML.encode())
        )
        await api.get_paper("2401.00001v2")
        request = route.calls[0].request
        assert "v2" not in str(request.url)

    @respx.mock
    async def test_get_paper_strips_v3(self, api_cleanup):
        api = api_cleanup
        route = respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=SAMPLE_ENTRY_XML.encode())
        )
        await api.get_paper("2401.00001v3")
        request = route.calls[0].request
        assert "v3" not in str(request.url)

    @respx.mock
    async def test_get_paper_not_found_empty_feed(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(200, content=EMPTY_FEED_XML.encode())
        )
        paper = await api.get_paper("9999.99999")
        assert paper is None

    @respx.mock
    async def test_get_paper_http_error(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(
            return_value=httpx.Response(404, content=b"Not Found")
        )
        paper = await api.get_paper("2401.00001")
        assert paper is None

    @respx.mock
    async def test_get_paper_network_error(self, api_cleanup):
        api = api_cleanup
        respx.get(api.base_url).mock(side_effect=httpx.ConnectError("Connection refused"))
        paper = await api.get_paper("2401.00001")
        assert paper is None


# ---------------------------------------------------------------------------
# ArxivAPI._parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_parse_valid_xml(self, api):
        papers = api._parse_response(SAMPLE_ENTRY_XML.encode())
        assert len(papers) == 1
        assert papers[0].title == "Test Paper on Machine Learning"
        assert papers[0].authors == ["Alice Smith", "Bob Jones"]

    def test_parse_multiple_entries(self, api):
        papers = api._parse_response(MULTI_ENTRY_XML.encode())
        assert len(papers) == 2

    def test_parse_empty_feed(self, api):
        papers = api._parse_response(EMPTY_FEED_XML.encode())
        assert papers == []

    def test_parse_malformed_xml(self, api):
        papers = api._parse_response(MALFORMED_XML)
        assert papers == []

    def test_parse_empty_bytes(self, api):
        papers = api._parse_response(b"")
        assert papers == []

    def test_parse_entry_missing_optional_fields(self, api):
        papers = api._parse_response(ENTRY_MISSING_FIELDS_XML.encode())
        assert len(papers) == 1
        paper = papers[0]
        assert paper.title == "Unknown Title"
        assert paper.authors == []
        assert paper.abstract == ""
        assert paper.categories == []
        assert paper.pdf_url == ""

    def test_parse_multiline_title(self, api):
        papers = api._parse_response(ENTRY_MULTILINE_TITLE_XML.encode())
        assert len(papers) == 1
        # newlines should be replaced with spaces and stripped
        assert "\n" not in papers[0].title
        assert "Spans Multiple Lines" in papers[0].title

    def test_parse_entry_no_pdf_link(self, api):
        papers = api._parse_response(MULTI_ENTRY_XML.encode())
        # second entry has no PDF link
        assert papers[1].pdf_url == ""

    def test_parse_extracts_published_date_only(self, api):
        papers = api._parse_response(SAMPLE_ENTRY_XML.encode())
        # published should be date only (first 10 chars)
        assert papers[0].published == "2024-01-15"
        assert len(papers[0].published) == 10


# ---------------------------------------------------------------------------
# ArxivAPI.close
# ---------------------------------------------------------------------------

class TestClose:
    @respx.mock
    async def test_close(self):
        api = ArxivAPI()
        await api.close()
        # After closing, making a request should fail
        with pytest.raises(Exception):
            await api.http_client.get("https://example.com")
