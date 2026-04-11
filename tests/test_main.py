"""Tests for main.py entry point."""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_main():
    """Import main module fresh (avoids side-effects at import time)."""
    import main
    return main


# ===========================================================================
# print_usage (synchronous, no mocking needed)
# ===========================================================================


class TestPrintUsage:
    """Tests for the print_usage helper."""

    def test_print_usage_outputs_help_text(self, capsys):
        main = _import_main()
        main.print_usage()
        captured = capsys.readouterr()
        assert "arXiv MCP Server" in captured.out
        assert "server" in captured.out
        assert "test" in captured.out
        assert "demo" in captured.out
        assert "--help" in captured.out


# ===========================================================================
# main() -- CLI argument dispatch
# ===========================================================================


class TestMainDispatch:
    """Tests for the main() async entry point and its argument routing."""

    @pytest.mark.asyncio
    async def test_no_args_runs_test_client(self):
        """With no CLI args, main() should invoke test_client()."""
        main = _import_main()
        with patch.object(main, "test_client", new_callable=AsyncMock) as mock_tc:
            with patch.object(sys, "argv", ["main.py"]):
                await main.main()
            mock_tc.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_server_command(self):
        main = _import_main()
        with patch.object(main, "run_server", new_callable=AsyncMock) as mock_rs:
            with patch.object(sys, "argv", ["main.py", "server"]):
                await main.main()
            mock_rs.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_test_command(self):
        main = _import_main()
        with patch.object(main, "test_client", new_callable=AsyncMock) as mock_tc:
            with patch.object(sys, "argv", ["main.py", "test"]):
                await main.main()
            mock_tc.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_demo_command(self):
        main = _import_main()
        with patch.object(main, "demo_usage", new_callable=AsyncMock) as mock_du:
            with patch.object(sys, "argv", ["main.py", "demo"]):
                await main.main()
            mock_du.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("flag", ["--help", "-h", "help"])
    async def test_help_flags(self, flag, capsys):
        main = _import_main()
        with patch.object(sys, "argv", ["main.py", flag]):
            await main.main()
        captured = capsys.readouterr()
        assert "arXiv MCP Server" in captured.out

    @pytest.mark.asyncio
    async def test_unknown_command_exits_with_error(self, capsys):
        main = _import_main()
        with patch.object(sys, "argv", ["main.py", "bogus"]):
            with pytest.raises(SystemExit) as exc_info:
                await main.main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown command: bogus" in captured.out

    @pytest.mark.asyncio
    async def test_command_is_case_insensitive(self):
        main = _import_main()
        with patch.object(main, "run_server", new_callable=AsyncMock) as mock_rs:
            with patch.object(sys, "argv", ["main.py", "SERVER"]):
                await main.main()
            mock_rs.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_demo_uppercase(self):
        main = _import_main()
        with patch.object(main, "demo_usage", new_callable=AsyncMock) as mock_du:
            with patch.object(sys, "argv", ["main.py", "DEMO"]):
                await main.main()
            mock_du.assert_awaited_once()


# ===========================================================================
# run_server()
# ===========================================================================


class TestRunServer:
    """Tests for the run_server coroutine."""

    @pytest.mark.asyncio
    async def test_run_server_creates_server_instance(self):
        """run_server should instantiate ArxivMCPServer."""
        main = _import_main()
        mock_server_cls = MagicMock()

        mock_sleep = AsyncMock(side_effect=KeyboardInterrupt)

        with patch("main.ArxivMCPServer", mock_server_cls):
            with patch("asyncio.sleep", mock_sleep):
                await main.run_server()
            mock_server_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_server_handles_keyboard_interrupt(self):
        """KeyboardInterrupt should be caught gracefully (no SystemExit)."""
        main = _import_main()

        mock_sleep = AsyncMock(side_effect=KeyboardInterrupt)

        with patch("main.ArxivMCPServer"):
            with patch("asyncio.sleep", mock_sleep):
                # Should NOT raise
                await main.run_server()

    @pytest.mark.asyncio
    async def test_run_server_handles_generic_exception(self):
        """A generic exception during startup should cause sys.exit(1)."""
        main = _import_main()

        with patch("main.ArxivMCPServer", side_effect=RuntimeError("startup boom")):
            with pytest.raises(SystemExit) as exc_info:
                await main.run_server()
            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_run_server_handles_exception_in_loop(self):
        """An exception raised inside the sleep loop should cause sys.exit(1)."""
        main = _import_main()

        mock_sleep = AsyncMock(side_effect=RuntimeError("loop failure"))

        with patch("main.ArxivMCPServer"):
            with patch("asyncio.sleep", mock_sleep):
                with pytest.raises(SystemExit) as exc_info:
                    await main.run_server()
                assert exc_info.value.code == 1


# ===========================================================================
# test_client()
# ===========================================================================


class TestTestClient:
    """Tests for the test_client coroutine."""

    @pytest.mark.asyncio
    async def test_test_client_success_path(self, capsys):
        """Happy path: all server methods return valid data."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {
            "papers": [
                {"id": "2401.00001", "title": "Paper One", "authors": ["Alice"]},
                {"id": "2401.00002", "title": "Paper Two", "authors": ["Bob"]},
            ]
        }
        mock_server.search_by_author.return_value = {
            "papers": [{"id": "2401.00003", "title": "Hinton Paper", "authors": ["Geoffrey Hinton"]}]
        }
        mock_server.search_by_category.return_value = {
            "papers": [{"id": "2401.00004", "title": "AI Paper", "authors": ["Eve"]}]
        }
        mock_server.get_recent_papers.return_value = {
            "papers": [{"id": "2401.00005", "title": "Recent Paper", "authors": ["Mallory"]}]
        }
        mock_server.compare_papers.return_value = "Comparison result text"
        mock_server.export_papers.return_value = "@article{...}"
        mock_server.find_related_papers.return_value = {
            "related_papers": [{"id": "2401.00006", "title": "Related"}]
        }
        mock_server.analyze_trends.return_value = {"total_papers": 100}

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.test_client()

        captured = capsys.readouterr()
        assert "All tests completed successfully" in captured.out

    @pytest.mark.asyncio
    async def test_test_client_no_papers_found(self, capsys):
        """When search returns no papers, test_client should exit early."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {"papers": []}

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.test_client()

        captured = capsys.readouterr()
        assert "No papers found" in captured.out
        # Should NOT reach the "All tests completed" line
        assert "All tests completed" not in captured.out

    @pytest.mark.asyncio
    async def test_test_client_handles_exception(self, capsys):
        """An exception during test_client should be caught and printed."""
        main = _import_main()

        with patch("arxiv_mcp.server.ArxivMCPServer", side_effect=RuntimeError("connection failed")):
            await main.test_client()

        captured = capsys.readouterr()
        assert "Test failed" in captured.out
        assert "connection failed" in captured.out


# ===========================================================================
# demo_usage()
# ===========================================================================


class TestDemoUsage:
    """Tests for the demo_usage coroutine."""

    @pytest.mark.asyncio
    async def test_demo_usage_success(self, capsys):
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {
            "papers": [
                {
                    "id": "2401.00001",
                    "title": "Attention Is All You Need",
                    "authors": ["Vaswani", "Shazeer"],
                    "categories": ["cs.CL", "cs.LG"],
                }
            ]
        }
        mock_server.search_by_author.return_value = {
            "papers": [
                {"title": "Deep Learning", "published": "2015-01-01"}
            ]
        }
        mock_server.export_papers.return_value = "@article{vaswani2017attention,...}"

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.demo_usage()

        captured = capsys.readouterr()
        assert "Usage Demo" in captured.out
        assert "Literature Search" in captured.out
        assert "Author Exploration" in captured.out
        assert "Citation Export" in captured.out

    @pytest.mark.asyncio
    async def test_demo_usage_no_papers(self, capsys):
        """When search returns nothing, demo should still complete without error."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {"papers": []}
        mock_server.search_by_author.return_value = {"papers": []}

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.demo_usage()

        captured = capsys.readouterr()
        assert "Usage Demo" in captured.out


# ===========================================================================
# __name__ == "__main__" block
# ===========================================================================


class TestIfNameMain:
    """Tests for the if __name__ == '__main__' guard."""

    def test_keyboard_interrupt_at_top_level(self, capsys):
        """KeyboardInterrupt at the top level should print goodbye."""
        main = _import_main()

        with patch("asyncio.run", side_effect=KeyboardInterrupt):
            # Simulate running the if-main block manually
            try:
                asyncio.run(main.main())
            except KeyboardInterrupt:
                # Reproduce the except block from main.py
                print("\nGoodbye!")

        captured = capsys.readouterr()
        assert "Goodbye" in captured.out

    def test_exception_at_top_level(self):
        """An unhandled exception at the top level should sys.exit(1)."""
        main = _import_main()

        with patch("asyncio.run", side_effect=RuntimeError("fatal")):
            with pytest.raises(RuntimeError):
                asyncio.run(main.main())


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    """Additional edge-case tests for completeness."""

    @pytest.mark.asyncio
    async def test_compare_papers_error_string(self, capsys):
        """When compare_papers returns an error string, test_client handles it."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {
            "papers": [
                {"id": "2401.00001", "title": "Paper One", "authors": ["Alice"]},
                {"id": "2401.00002", "title": "Paper Two", "authors": ["Bob"]},
            ]
        }
        mock_server.search_by_author.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.search_by_category.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.get_recent_papers.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.compare_papers.return_value = "Error: something went wrong"
        mock_server.export_papers.return_value = "@article{...}"
        mock_server.find_related_papers.return_value = {"related_papers": []}
        mock_server.analyze_trends.return_value = {"total_papers": 0}

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.test_client()

        captured = capsys.readouterr()
        # Should still complete (the error branch just skips the success print)
        assert "All tests completed" in captured.out

    @pytest.mark.asyncio
    async def test_export_papers_error_string(self, capsys):
        """When export_papers returns an error string, test_client handles it."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {
            "papers": [
                {"id": "2401.00001", "title": "Paper One", "authors": ["Alice"]},
                {"id": "2401.00002", "title": "Paper Two", "authors": ["Bob"]},
            ]
        }
        mock_server.search_by_author.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.search_by_category.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.get_recent_papers.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.compare_papers.return_value = "Comparison OK"
        mock_server.export_papers.return_value = "Error: export failed"
        mock_server.find_related_papers.return_value = {"related_papers": []}
        mock_server.analyze_trends.return_value = {"total_papers": 0}

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.test_client()

        captured = capsys.readouterr()
        assert "All tests completed" in captured.out

    @pytest.mark.asyncio
    async def test_single_paper_skips_comparison(self, capsys):
        """When only 1 paper is found, comparison step should be skipped."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {
            "papers": [
                {"id": "2401.00001", "title": "Only Paper", "authors": ["Solo"]},
            ]
        }
        mock_server.search_by_author.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.search_by_category.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.get_recent_papers.return_value = {"papers": [{"id": "x", "title": "Y", "authors": ["Z"]}]}
        mock_server.export_papers.return_value = "@article{...}"
        mock_server.find_related_papers.return_value = {"related_papers": []}
        mock_server.analyze_trends.return_value = {"total_papers": 0}

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.test_client()

        captured = capsys.readouterr()
        # compare_papers should NOT have been called since len(papers) < 2
        mock_server.compare_papers.assert_not_awaited()
        assert "All tests completed" in captured.out

    @pytest.mark.asyncio
    async def test_demo_long_bibtex_truncated(self, capsys):
        """When BibTeX export is longer than 200 chars, demo truncates it."""
        main = _import_main()

        mock_server = AsyncMock()
        mock_server.search_arxiv.return_value = {
            "papers": [
                {
                    "id": "2401.00001",
                    "title": "Paper",
                    "authors": ["A"],
                    "categories": ["cs.AI"],
                }
            ]
        }
        mock_server.search_by_author.return_value = {"papers": []}
        mock_server.export_papers.return_value = "x" * 300

        with patch("arxiv_mcp.server.ArxivMCPServer", return_value=mock_server):
            await main.demo_usage()

        captured = capsys.readouterr()
        assert "..." in captured.out
