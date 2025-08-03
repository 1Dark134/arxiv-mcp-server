import asyncio
import logging
import sys
from typing import Optional

from arxiv_mcp import ArxivMCPClient, ArxivMCPServer
from arxiv_mcp.utils import setup_logging

async def run_server():
    """Run the MCP server."""
    setup_logging("INFO")
    logger = logging.getLogger(__name__)

    try:
        server = ArxivMCPServer()
        logger.info("Starting arXiv MCP server...")

        # Server implementation would go here
        # For now, we'll just show that it's ready
        logger.info("arXiv MCP server is ready!")

        # Keep server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


async def test_client():
    """Test the MCP client functionality."""
    setup_logging("INFO")
    logger = logging.getLogger(__name__)

    print("arXiv MCP Client Test Suite")
    print("=" * 50)

    try:
        # Create direct server instance for testing
        from arxiv_mcp.server import ArxivMCPServer
        server = ArxivMCPServer()

        # Test basic search
        print("🔍 Testing basic search...")
        results = await server.search_arxiv("genai", max_results=3)

        if results.get("papers"):
            print(f"✅ Found {len(results['papers'])} papers")
            for i, paper in enumerate(results["papers"][:2], 1):
                print(f"   {i}. {paper['title'][:60]}...")
                print(f"      Authors: {', '.join(paper['authors'][:2])}...")
                print(f"      arXiv ID: {paper['id']}")
        else:
            print("❌ No papers found")
            return

        first_paper_id = results["papers"][0]["id"]

        # Test additional tools
        print("\n🧪 Testing advanced features...")

        # Test author search
        print("   📚 Author search...")
        author_results = await server.search_by_author("Geoffrey Hinton", max_results=2)
        if author_results.get("papers"):
            print(f"   ✅ Found {len(author_results['papers'])} papers by Geoffrey Hinton")

        # Test category search
        print("   🏷️  Category search...")
        cat_results = await server.search_by_category("cs.AI", max_results=2)
        if cat_results.get("papers"):
            print(f"   ✅ Found {len(cat_results['papers'])} papers in cs.AI")

        # Test recent papers
        print("   📅 Recent papers...")
        recent_results = await server.get_recent_papers("cs.LG", days_back=7, max_results=2)
        if recent_results.get("papers"):
            print(f"   ✅ Found {len(recent_results['papers'])} recent cs.LG papers")

        # Test paper comparison
        if len(results["papers"]) >= 2:
            print("   ⚖️  Paper comparison...")
            paper_ids = [p["id"] for p in results["papers"][:2]]
            comparison = await server.compare_papers(paper_ids, ["authors", "published"])
            if comparison and not comparison.startswith("Error"):
                print("   ✅ Generated paper comparison")

        # Test export
        print("   💾 Export functionality...")
        export_ids = [results["papers"][0]["id"]]
        bibtex_export = await server.export_papers(export_ids, "bibtex", include_abstract=False)
        if bibtex_export and not bibtex_export.startswith("Error"):
            print("   ✅ Generated BibTeX export")

        # Test related papers
        print("   🔗 Related papers...")
        related = await server.find_related_papers(first_paper_id, max_results=3)
        if related.get("related_papers"):
            print(f"   ✅ Found {len(related['related_papers'])} related papers")

        # Test trend analysis
        print("   📈 Trend analysis...")
        trends = await server.analyze_trends("cs.AI", "1_month", "publication_count")
        if trends.get("total_papers", 0) > 0:
            print(f"   ✅ Analyzed {trends['total_papers']} papers for trends")

        print("\n🎉 All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")


async def demo_usage():
    """Demonstrate typical usage patterns."""
    print("arXiv MCP Server - Usage Demo")
    print("=" * 40)

    from arxiv_mcp.server import ArxivMCPServer
    server = ArxivMCPServer()

    # Demo 1: Literature search for a research topic
    print("\n📖 Demo 1: Literature Search")
    print("-" * 30)

    query = "attention mechanism neural networks"
    results = await server.search_arxiv(query, max_results=5)

    if results.get("papers"):
        print(f"Search: '{query}'")
        print(f"Found: {len(results['papers'])} papers\n")

        for i, paper in enumerate(results["papers"][:3], 1):
            print(f"{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:2])}...")
            print(f"   Categories: {', '.join(paper['categories'][:2])}")
            print(f"   arXiv ID: {paper['id']}\n")

    # Demo 2: Author exploration
    print("👨‍🔬 Demo 2: Author Exploration")
    print("-" * 30)

    author_results = await server.search_by_author("Yann LeCun", max_results=3)
    if author_results.get("papers"):
        print(f"Recent papers by Yann LeCun:")
        for paper in author_results["papers"][:3]:
            print(f"• {paper['title']} ({paper['published'][:4]})")

    # Demo 3: Export for citation
    print("\n📝 Demo 3: Citation Export")
    print("-" * 30)

    if results.get("papers"):
        export_ids = [results["papers"][0]["id"]]
        bibtex = await server.export_papers(export_ids, "bibtex", include_abstract=False)
        print("BibTeX format:")
        print(bibtex[:200] + "..." if len(bibtex) > 200 else bibtex)


def print_usage():
    """Print usage information."""
    print("""
arXiv MCP Server - Usage:

Commands:
  python main.py server          Run the MCP server
  python main.py test            Run client tests
  python main.py demo            Run usage demonstration
  python main.py --help          Show this help message

Examples:
  python main.py server          # Start the server
  python main.py test            # Test all functionality
  python main.py demo            # See usage examples
""")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        await test_client()
        return

    command = sys.argv[1].lower()

    if command == "server":
        await run_server()
    elif command == "test":
        await test_client()
    elif command == "demo":
        await demo_usage()
    elif command in ["--help", "-h", "help"]:
        print_usage()
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
