import json
import csv
from io import StringIO
from typing import List, Dict, Any

from .models import Paper, ExportConfig


class PaperExporter:
    """Export papers in various formats."""

    @staticmethod
    def export_papers(
            papers: List[Paper],
            config: ExportConfig
    ) -> str:
        """Export papers based on configuration."""
        if config.format == "bibtex":
            return PaperExporter._export_bibtex(papers, config)
        elif config.format == "json":
            return PaperExporter._export_json(papers, config)
        elif config.format == "csv":
            return PaperExporter._export_csv(papers, config)
        elif config.format == "markdown":
            return PaperExporter._export_markdown(papers, config)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

    @staticmethod
    def _export_bibtex(papers: List[Paper], config: ExportConfig) -> str:
        """Export papers in BibTeX format."""
        bibtex_entries = []

        for paper in papers:
            arxiv_id = paper.id.replace('.', '_').replace('/', '_')
            title = paper.title.replace('{', '\\{').replace('}', '\\}')
            authors = ' and '.join(paper.authors)
            year = paper.published[:4] if paper.published else ''

            entry = f"""@article{{{arxiv_id},
  title={{{title}}},
  author={{{authors}}},
  journal={{arXiv preprint arXiv:{paper.id}}},
  year={{{year}}}"""

            if config.include_urls:
                entry += f",\n  url={{https://export.arxiv.org/abs/{paper.id}}}"

            if config.include_abstract and config.include_abstract:
                abstract = paper.abstract.replace('{', '\\{').replace('}', '\\}')
                entry += f",\n  abstract={{{abstract}}}"

            if config.include_categories and paper.categories:
                categories = ', '.join(paper.categories)
                entry += f",\n  note={{Categories: {categories}}}"

            entry += "\n}"
            bibtex_entries.append(entry)

        return "\n\n".join(bibtex_entries)

    @staticmethod
    def _export_json(papers: List[Paper], config: ExportConfig) -> str:
        """Export papers in JSON format."""
        paper_dicts = []
        for paper in papers:
            paper_dict = paper.to_dict()

            if not config.include_abstract:
                paper_dict.pop('abstract', None)
            if not config.include_categories:
                paper_dict.pop('categories', None)
            if not config.include_urls:
                paper_dict.pop('arxiv_url', None)
                paper_dict.pop('pdf_url', None)

            paper_dicts.append(paper_dict)

        return json.dumps(paper_dicts, indent=2)

    @staticmethod
    def _export_csv(papers: List[Paper], config: ExportConfig) -> str:
        """Export papers in CSV format."""
        output = StringIO()
        fieldnames = ['id', 'title', 'authors', 'published']

        if config.include_categories:
            fieldnames.append('categories')
        if config.include_urls:
            fieldnames.extend(['arxiv_url', 'pdf_url'])
        if config.include_abstract:
            fieldnames.append('abstract')

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for paper in papers:
            row = {
                'id': paper.id,
                'title': paper.title,
                'authors': '; '.join(paper.authors),
                'published': paper.published,
            }

            if config.include_categories:
                row['categories'] = '; '.join(paper.categories)
            if config.include_urls:
                row['arxiv_url'] = paper.arxiv_url
                row['pdf_url'] = paper.pdf_url
            if config.include_abstract:
                row['abstract'] = paper.abstract

            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def _export_markdown(papers: List[Paper], config: ExportConfig) -> str:
        """Export papers in Markdown format."""
        markdown_content = "# arXiv Papers Export\n\n"

        for i, paper in enumerate(papers, 1):
            markdown_content += f"## {i}. {paper.title}\n\n"
            markdown_content += f"**Authors:** {', '.join(paper.authors)}  \n"
            markdown_content += f"**arXiv ID:** [{paper.id}](https://exportarxiv.org/abs/{paper.id})  \n"
            markdown_content += f"**Published:** {paper.published}  \n"

            if config.include_categories and paper.categories:
                markdown_content += f"**Categories:** {', '.join(paper.categories)}  \n"

            if config.include_urls:
                markdown_content += f"**PDF:** [Download](https://export.arxiv.org/pdf/{paper.id}.pdf)  \n"

            markdown_content += "\n"

            if config.include_abstract:
                markdown_content += f"**Abstract:**  \n{paper.abstract}\n\n"

            markdown_content += "---\n\n"

        return markdown_content