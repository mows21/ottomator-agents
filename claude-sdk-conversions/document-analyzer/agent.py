"""
Document Analysis Agent - Claude SDK Version

Integrates: docling-rag-agent capabilities
Framework: Claude Agent SDK + Docling

This agent uses Docling for document processing (PDF, Word, etc.)
and Claude SDK for intelligent analysis and Q&A.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from docling.document_converter import DocumentConverter

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.base_agent import BaseClaudeAgent, AgentConfig

load_dotenv()

console = Console()


class DocumentAnalyzer:
    """
    Document analysis agent using Docling + Claude SDK.

    Features:
    - Supports PDF, DOCX, PPTX, XLSX, HTML, and more
    - Converts documents to structured markdown
    - Intelligent Q&A over documents
    - Multi-document analysis
    - Table extraction and analysis
    """

    def __init__(self, documents_dir: Optional[str] = None):
        self.documents_dir = documents_dir or os.getenv('DOCUMENTS_DIR', './documents')
        self.converter = DocumentConverter()
        self.loaded_documents: Dict[str, str] = {}  # filename -> markdown content

        system_prompt = """You are an expert document analyst.

Your capabilities:
1. Analyze document content deeply
2. Extract key information and insights
3. Answer questions about documents accurately
4. Compare and synthesize across multiple documents
5. Identify patterns, trends, and relationships

When analyzing documents:
- Provide specific citations (page numbers, sections)
- Highlight important findings
- Explain complex content clearly
- Note any ambiguities or missing information
"""

        config = AgentConfig(
            system_prompt=system_prompt,
            model="sonnet",
        )

        self.agent = BaseClaudeAgent(config)

    def list_available_documents(self) -> List[str]:
        """List all supported documents in the documents directory."""
        if not os.path.exists(self.documents_dir):
            return []

        supported_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.html', '.htm', '.md', '.txt']

        docs = []
        for root, _, files in os.walk(self.documents_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    rel_path = os.path.relpath(os.path.join(root, file), self.documents_dir)
                    docs.append(rel_path)

        return sorted(docs)

    async def load_document(self, file_path: str) -> Dict[str, Any]:
        """
        Load and convert a document to markdown using Docling.

        Args:
            file_path: Path to document (relative to documents_dir or absolute)

        Returns:
            Dictionary with document info and content
        """
        # Handle both absolute and relative paths
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.documents_dir, file_path)
        else:
            full_path = file_path

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Document not found: {full_path}")

        file_name = os.path.basename(full_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        console.print(f"\n[cyan]Loading document:[/cyan] {file_name}")

        # Text files - read directly
        if file_ext in ['.md', '.txt']:
            with open(full_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        else:
            # Use Docling for other formats
            console.print(f"[dim]Converting {file_ext} with Docling...[/dim]")

            try:
                result = self.converter.convert(full_path)
                markdown_content = result.document.export_to_markdown()
                console.print(f"[green]✓ Converted to markdown ({len(markdown_content)} chars)[/green]")
            except Exception as e:
                raise Exception(f"Failed to convert document: {e}")

        # Store in memory
        self.loaded_documents[file_name] = markdown_content

        return {
            "filename": file_name,
            "path": full_path,
            "content_length": len(markdown_content),
            "content": markdown_content
        }

    async def analyze_document(self, file_path: str, question: Optional[str] = None) -> str:
        """
        Analyze a document and optionally answer a question about it.

        Args:
            file_path: Path to document
            question: Optional question to answer

        Returns:
            Analysis or answer
        """
        # Load document
        doc_info = await self.load_document(file_path)

        if question:
            prompt = f"""Document: {doc_info['filename']}

Content:
{doc_info['content']}

---

Question: {question}

Analyze the document and answer the question. Provide specific citations where relevant.
"""
        else:
            prompt = f"""Document: {doc_info['filename']}

Content:
{doc_info['content']}

---

Provide a comprehensive analysis of this document including:
1. Main topics and themes
2. Key findings or conclusions
3. Important data or statistics
4. Notable insights
5. Any concerns or limitations
"""

        console.print("\n[cyan]Analyzing document...[/cyan]\n")

        result = await self.agent.query(prompt)
        return result

    async def compare_documents(self, file_paths: List[str], comparison_query: str) -> str:
        """
        Compare multiple documents.

        Args:
            file_paths: List of document paths
            comparison_query: What to compare or analyze

        Returns:
            Comparative analysis
        """
        # Load all documents
        documents_content = []

        console.print(f"\n[cyan]Loading {len(file_paths)} documents for comparison...[/cyan]")

        for file_path in file_paths:
            doc_info = await self.load_document(file_path)
            documents_content.append(f"## Document: {doc_info['filename']}\n\n{doc_info['content']}")

        # Combine all documents
        combined_content = "\n\n" + "\n\n---\n\n".join(documents_content)

        prompt = f"""Documents to Compare:
{combined_content}

---

Comparison Task: {comparison_query}

Analyze these documents comparatively. Highlight similarities, differences, and relationships.
"""

        console.print("\n[cyan]Comparing documents...[/cyan]\n")

        result = await self.agent.query(prompt)
        return result

    async def interactive_mode(self):
        """Run the agent in interactive CLI mode."""
        console.print("\n[bold green]" + "=" * 70 + "[/bold green]")
        console.print("[bold green]Document Analysis Agent - Claude SDK + Docling[/bold green]")
        console.print("[bold green]" + "=" * 70 + "[/bold green]")

        console.print(f"\n[cyan]Documents Directory:[/cyan] {os.path.abspath(self.documents_dir)}")

        # List available documents
        available_docs = self.list_available_documents()

        if available_docs:
            console.print(f"\n[cyan]Available Documents ({len(available_docs)}):[/cyan]")
            for i, doc in enumerate(available_docs[:10], 1):
                console.print(f"  {i}. {doc}")
            if len(available_docs) > 10:
                console.print(f"  ... and {len(available_docs) - 10} more")
        else:
            console.print(f"\n[yellow]No documents found in {self.documents_dir}[/yellow]")
            console.print("[dim]Tip: Place PDF, DOCX, or other documents in the documents folder[/dim]")

        console.print("\n[bold cyan]Commands:[/bold cyan]")
        console.print("  [cyan]load <file>[/cyan] - Load a document")
        console.print("  [cyan]analyze <file> [question][/cyan] - Analyze a document")
        console.print("  [cyan]compare <file1> <file2> [query][/cyan] - Compare documents")
        console.print("  [cyan]list[/cyan] - List available documents")
        console.print("  [cyan]exit[/cyan] - Quit")

        console.print()

        await self.agent.start_session()

        while True:
            try:
                user_input = console.input("\n[bold cyan]Command:[/bold cyan] ")

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("\n[bold green]Goodbye![/bold green]\n")
                    break

                if not user_input.strip():
                    continue

                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()

                # List command
                if command == 'list':
                    docs = self.list_available_documents()
                    console.print(f"\n[cyan]Available Documents ({len(docs)}):[/cyan]")
                    for doc in docs:
                        console.print(f"  • {doc}")
                    continue

                # Load command
                if command == 'load':
                    if len(parts) < 2:
                        console.print("[yellow]Usage: load <file>[/yellow]")
                        continue

                    file_path = parts[1]
                    try:
                        doc_info = await self.load_document(file_path)
                        console.print(f"\n[green]✓ Loaded: {doc_info['filename']}[/green]")
                        console.print(f"  Content length: {doc_info['content_length']} chars")
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                    continue

                # Analyze command
                if command == 'analyze':
                    if len(parts) < 2:
                        console.print("[yellow]Usage: analyze <file> [question][/yellow]")
                        continue

                    args = parts[1].split(maxsplit=1)
                    file_path = args[0]
                    question = args[1] if len(args) > 1 else None

                    try:
                        result = await self.analyze_document(file_path, question)
                        console.print("\n[bold magenta]Analysis:[/bold magenta]\n")
                        console.print(Markdown(result))
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                    continue

                # Compare command
                if command == 'compare':
                    if len(parts) < 2:
                        console.print("[yellow]Usage: compare <file1> <file2> [query][/yellow]")
                        continue

                    args = parts[1].split()
                    if len(args) < 2:
                        console.print("[yellow]Need at least 2 files to compare[/yellow]")
                        continue

                    files = []
                    query_parts = []
                    for arg in args:
                        if os.path.exists(os.path.join(self.documents_dir, arg)):
                            files.append(arg)
                        else:
                            query_parts.append(arg)

                    comparison_query = " ".join(query_parts) if query_parts else "Compare these documents"

                    try:
                        result = await self.compare_documents(files, comparison_query)
                        console.print("\n[bold magenta]Comparison:[/bold magenta]\n")
                        console.print(Markdown(result))
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                    continue

                # If loaded documents exist, treat as Q&A
                if self.loaded_documents:
                    all_docs = "\n\n---\n\n".join([
                        f"## {name}\n\n{content}"
                        for name, content in self.loaded_documents.items()
                    ])

                    prompt = f"""Loaded Documents:
{all_docs}

---

Question: {user_input}

Answer based on the loaded documents.
"""

                    result = await self.agent.query(prompt)
                    console.print("\n[bold magenta]Answer:[/bold magenta]\n")
                    console.print(Markdown(result))
                else:
                    console.print("[yellow]No documents loaded. Use 'load <file>' or 'analyze <file>'[/yellow]")

            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
                continue
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")
                import traceback
                traceback.print_exc()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Document Analysis Agent")
    parser.add_argument(
        "--documents-dir",
        "-d",
        help="Directory containing documents (default: ./documents)"
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Analyze a specific file"
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Question to ask about the document"
    )

    args = parser.parse_args()

    agent = DocumentAnalyzer(documents_dir=args.documents_dir)

    if args.file:
        # Single file analysis mode
        question = " ".join(args.question) if args.question else None
        try:
            result = await agent.analyze_document(args.file, question)
            console.print("\n[bold magenta]Analysis:[/bold magenta]\n")
            console.print(Markdown(result))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    else:
        # Interactive mode
        await agent.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
