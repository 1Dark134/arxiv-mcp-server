# arXiv MCP Service Client

A comprehensive Model Context Protocol (MCP) implementation for interacting with arXiv.org, enabling AI assistants to search, retrieve, analyze, and export academic papers seamlessly.

## 🚀 Features

### Core Functionality
- **Paper Search**: Advanced search with keywords, authors, titles, and categories
- **Paper Retrieval**: Get detailed metadata for specific arXiv papers
- **Smart Summaries**: Generate formatted paper summaries with key information

### Advanced Tools
- **Author Search**: Find all papers by specific researchers
- **Category Browsing**: Explore papers in specific arXiv categories (cs.AI, cs.LG, etc.)
- **Recent Papers**: Get latest publications with customizable time ranges
- **Paper Comparison**: Side-by-side analysis of multiple papers
- **Related Papers**: Discover papers related to a given work using intelligent matching
- **Citation Analysis**: Estimated citation metrics and impact analysis
- **Trend Analysis**: Research trend analysis with publication counts, top authors, and keyword frequency
- **Multi-format Export**: Export papers in BibTeX, JSON, CSV, and Markdown formats

## 📦 Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-mcp-client.git
cd arxiv-mcp-client

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Install dependencies
pip install mcp httpx

# Run the client
python arxiv_mcp_client.py
```

## 🛠️ Usage

### Basic Setup

```python
import asyncio
from arxiv_mcp_client import ArxivMCPClient

async def main():
    # Initialize client
    client = ArxivMCPClient()
    
    # Connect to MCP server
    await client.connect("arxiv_mcp_server.py")
    
    # Your code here...
    
    # Close connection
    await client.close()

asyncio.run(main())
```

### Search Examples

```python
# General search
results = await client.search_papers("transformer neural networks", max_results=10)

# Search by author
papers = await client.search_by_author("Geoffrey Hinton", max_results=20)

# Search by category
ai_papers = await client.search_by_category("cs.AI", max_results=15)

# Get recent papers
recent = await client.get_recent_papers("cs.LG", days_back=7, max_results=10)
```

### Paper Analysis

```python
# Get paper details
paper = await client.get_paper_details("2301.07041")

# Get formatted summary
summary = await client.get_paper_summary("2301.07041")

# Compare papers
comparison = await client.compare_papers(
    ["2301.07041", "2302.13971"], 
    comparison_fields=["authors", "abstract", "categories"]
)

# Find related papers
related = await client.find_related_papers("2301.07041", max_results=10)
```

### Export and Analysis

```python
# Export to BibTeX
bibtex = await client.export_papers(
    ["2301.07041", "2302.13971"], 
    format="bibtex", 
    include_abstract=True
)

# Analyze research trends
trends = await client.analyze_trends(
    category="cs.AI", 
    time_period="3_months", 
    analysis_type="top_authors"
)
```

## 🔧 Available Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `search_arxiv` | General paper search | `query`, `max_results`, `sort_by` |
| `get_paper` | Get specific paper details | `arxiv_id` |
| `summarize_paper` | Generate formatted summary | `arxiv_id` |
| `search_by_author` | Find papers by author | `author_name`, `max_results` |
| `search_by_category` | Browse category papers | `category`, `max_results`, `sort_by` |
| `get_recent_papers` | Get latest publications | `category`, `days_back`, `max_results` |
| `compare_papers` | Compare multiple papers | `arxiv_ids`, `comparison_fields` |
| `find_related_papers` | Discover related work | `arxiv_id`, `max_results` |
| `get_paper_citations` | Citation analysis | `arxiv_id` |
| `analyze_trends` | Research trend analysis | `category`, `time_period`, `analysis_type` |
| `export_papers` | Multi-format export | `arxiv_ids`, `format`, `include_abstract` |

## 📊 Supported Categories

### Computer Science
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning  
- `cs.CV` - Computer Vision
- `cs.CL` - Computation and Language
- `cs.CR` - Cryptography and Security
- `cs.DB` - Databases
- `cs.DS` - Data Structures and Algorithms

### Mathematics
- `math.CO` - Combinatorics
- `math.ST` - Statistics Theory
- `math.PR` - Probability
- `math.OC` - Optimization and Control

### Physics
- `physics.comp-ph` - Computational Physics
- `physics.data-an` - Data Analysis
- `quant-ph` - Quantum Physics

[See full category list](https://arxiv.org/category_taxonomy)

## 📄 Export Formats

### BibTeX
```bibtex
@article{2301_07041,
  title={Title of the Paper},
  author={Author One and Author Two},
  journal={arXiv preprint arXiv:2301.07041},
  year={2023},
  url={https://arxiv.org/abs/2301.07041}
}
```

### JSON
```json
{
  "id": "2301.07041",
  "title": "Title of the Paper",
  "authors": ["Author One", "Author Two"],
  "abstract": "Paper abstract...",
  "published": "2023-01-17",
  "categories": ["cs.AI", "cs.LG"]
}
```

### CSV
```csv
id,title,authors,published,categories,url
2301.07041,Title of the Paper,"Author One; Author Two",2023-01-17,"cs.AI; cs.LG",https://arxiv.org/abs/2301.07041
```

## 🔍 Search Query Examples

### Basic Searches
```python
# Keyword search
await client.search_papers("neural networks")

# Multiple keywords
await client.search_papers("transformer attention mechanism")

# Exact phrase
await client.search_papers('"large language models"')
```

### Advanced Searches
```python
# Author search
await client.search_by_author("Yoshua Bengio")

# Category search  
await client.search_by_category("cs.AI")

# Recent papers in category
await client.get_recent_papers("cs.LG", days_back=14)
```

## 📈 Trend Analysis Types

### Publication Count Analysis
Tracks the number of papers published over time in a specific category.

```python
trends = await client.analyze_trends("cs.AI", "6_months", "publication_count")
# Returns: monthly publication counts
```

### Top Authors Analysis
Identifies the most prolific authors in a field over a given period.

```python
trends = await client.analyze_trends("cs.LG", "1_year", "top_authors")
# Returns: authors ranked by paper count
```

### Keyword Frequency Analysis
Analyzes the most common keywords in paper titles within a category.

```python
trends = await client.analyze_trends("cs.CV", "3_months", "keyword_frequency")
# Returns: keywords ranked by frequency
```

## 🚨 Error Handling

The client includes comprehensive error handling:

```python
try:
    results = await client.search_papers("machine learning")
    if "error" in results:
        print(f"Search failed: {results['error']}")
    else:
        print(f"Found {len(results['papers'])} papers")
except Exception as e:
    print(f"Connection error: {e}")
```

## 🔧 Configuration

### Rate Limiting
The client respects arXiv's API guidelines with built-in rate limiting and timeout handling.

### Customization
```python
# Custom timeout
client = ArxivMCPClient()
client.http_client = httpx.AsyncClient(timeout=60.0)

# Custom result limits
results = await client.search_papers("AI", max_results=50)  # Max: 100
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [arXiv.org](https://arxiv.org/) for providing free access to academic papers
- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- The open-source community for the underlying libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/arxiv-mcp-client/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/arxiv-mcp-client/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/arxiv-mcp-client/discussions)

---

**Made with ❤️ for the research community**