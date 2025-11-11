# Document Analysis Agent - Claude SDK + Docling

Intelligent document analysis using Claude SDK and Docling for document processing.

**Integrates**: `docling-rag-agent` capabilities
**Framework**: Claude Agent SDK + Docling

## Features

- **Multi-Format Support**: PDF, DOCX, PPTX, XLSX, HTML, Markdown, Text
- **Docling Integration**: Advanced document parsing and structure extraction
- **Intelligent Q&A**: Ask questions about document content
- **Multi-Document Analysis**: Compare and synthesize across documents
- **Table Extraction**: Automatically extract and analyze tables
- **Citation**: Specific references to document sections

## Why Docling?

Docling is a powerful document processing library that:
- Preserves document structure (headings, tables, lists)
- Handles complex PDFs with high accuracy
- Extracts tables in structured format
- Supports multiple document formats
- Converts everything to clean markdown

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Authentication

**Option A: Claude CLI (Recommended)**
```bash
claude auth login
```

**Option B: API Key**
```bash
export ANTHROPIC_API_KEY=your_key_here
```

Or create a `.env` file:
```env
ANTHROPIC_API_KEY=your_anthropic_key
DOCUMENTS_DIR=./documents  # Optional: custom documents directory
```

### 3. Prepare Documents

Create a `documents` directory and add your files:

```bash
mkdir documents
cp ~/Downloads/*.pdf documents/
```

Supported formats:
- PDF (`.pdf`)
- Microsoft Word (`.docx`, `.doc`)
- PowerPoint (`.pptx`, `.ppt`)
- Excel (`.xlsx`, `.xls`)
- HTML (`.html`, `.htm`)
- Markdown (`.md`)
- Text (`.txt`)

## Usage

### Interactive Mode

```bash
python agent.py
```

Example session:

```
======================================================================
Document Analysis Agent - Claude SDK + Docling
======================================================================

Documents Directory: /path/to/documents

Available Documents (5):
  1. research_paper.pdf
  2. financial_report.xlsx
  3. presentation.pptx
  4. notes.md
  5. contract.docx

Commands:
  load <file> - Load a document
  analyze <file> [question] - Analyze a document
  compare <file1> <file2> [query] - Compare documents
  list - List available documents
  exit - Quit

Command: analyze research_paper.pdf What are the key findings?

Loading document: research_paper.pdf
Converting .pdf with Docling...
✓ Converted to markdown (45230 chars)

Analyzing document...

Analysis:

The research paper presents three key findings:

1. **Performance Improvement**: The proposed method achieves 15% better
   accuracy compared to baseline approaches (see Table 2, page 5).

2. **Scalability**: The system scales linearly up to 1000 concurrent
   users without degradation (Section 4.2, page 8).

3. **Cost Reduction**: Implementation costs are reduced by 40% through
   optimization techniques (Figure 3, page 10).

...
```

### Single File Analysis

```bash
python agent.py --file research_paper.pdf "What are the key findings?"
```

### Compare Documents

```bash
# Interactive mode
Command: compare report_2024.pdf report_2025.pdf What changed between these reports?

# Or use Python directly
python agent.py  # then use compare command
```

## Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `list` | Show all available documents | `list` |
| `load <file>` | Load a document into memory | `load report.pdf` |
| `analyze <file> [question]` | Analyze document with optional question | `analyze report.pdf What is the revenue?` |
| `compare <file1> <file2> [query]` | Compare multiple documents | `compare old.pdf new.pdf What changed?` |
| `exit` | Quit the application | `exit` |

## Use Cases

### 1. Research Paper Analysis

```
Command: analyze research_paper.pdf

Result:
- Main research question and hypothesis
- Methodology overview
- Key findings with citations
- Limitations and future work
```

### 2. Financial Report Q&A

```
Command: analyze financial_report.xlsx What was the Q4 revenue?

Result:
- Extracts revenue figures from tables
- Provides context and comparisons
- Notes any important footnotes
```

### 3. Contract Review

```
Command: analyze contract.docx List all obligations and deadlines

Result:
- Structured list of all obligations
- Timeline with specific dates
- Key terms and conditions
```

### 4. Document Comparison

```
Command: compare v1.docx v2.docx

Result:
- Section-by-section comparison
- Added/removed content
- Changed terms or conditions
```

## Architecture

```
┌─────────────────────────────┐
│   User Query/Command        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   Document Analyzer         │
│   (Python)                  │
└──────────┬──────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌──────────────┐
│ Docling │  │ Claude SDK   │
│ Parser  │  │ Analysis     │
└─────────┘  └──────────────┘
     │              │
     └──────┬───────┘
            ▼
    ┌──────────────┐
    │   Response   │
    └──────────────┘
```

## Advanced Features

### Multi-Document Context

Load multiple documents and ask questions across them:

```
Command: load report_2023.pdf
Command: load report_2024.pdf
Command: How has revenue grown over these two years?
```

The agent will analyze both documents and provide comparative insights.

### Table Analysis

Docling automatically extracts tables in structured format:

```
Command: analyze spreadsheet.xlsx What are the top 5 products by revenue?
```

The agent can analyze table data intelligently.

### Citation and References

All answers include specific citations:

```
"The revenue increased by 25% (see Table 3, page 12)"
"As stated in Section 2.1 on page 5..."
```

## Performance Notes

- **PDF Processing**: ~2-5 seconds per page with Docling
- **Large Documents**: Documents over 100 pages are supported but may take longer
- **Concurrent Processing**: Can load multiple documents in parallel
- **Memory**: Loaded documents are kept in memory for faster Q&A

## Advantages Over Original docling-rag-agent

| Feature | docling-rag-agent | Claude SDK Version |
|---------|-------------------|-------------------|
| **Vector DB** | Requires PostgreSQL + pgvector | Not needed |
| **Embedding** | Requires OpenAI embeddings | Not needed |
| **Setup Complexity** | Database setup, migrations | Just install packages |
| **Query Speed** | Vector search + LLM | Direct LLM analysis |
| **Accuracy** | Depends on chunking/embeddings | Full document context |
| **Cost** | Embedding + storage + LLM | Just LLM |

## When to Use Vector DB vs Direct Analysis

**Use Direct Analysis (this agent)** when:
- Small to medium documents (< 50 pages)
- Need full context understanding
- Quick setup required
- Interactive exploration

**Use Vector DB (docling-rag-agent)** when:
- Large document collections (100+ documents)
- Frequent repeated queries
- Need semantic search across corpus
- Production RAG system

## Extending the Agent

### Add Custom Document Processing

```python
# In agent.py, extend DocumentAnalyzer class:

async def extract_tables(self, file_path: str) -> List[Dict]:
    """Extract all tables from document."""
    doc_info = await self.load_document(file_path)
    # Use Docling's table extraction
    result = self.converter.convert(doc_info['path'])
    tables = result.document.tables
    return tables
```

### Integration with Crawl4AI

```python
# Combine web scraping with document analysis:

from crawl4ai import AsyncWebCrawler

async def analyze_url(self, url: str, question: str) -> str:
    """Scrape and analyze web content."""
    crawler = AsyncWebCrawler()
    result = await crawler.crawl(url)
    # Use result.markdown as document content
    ...
```

## Troubleshooting

**Issue**: Docling conversion fails
- **Solution**: Ensure document is not corrupted. Try a different format or converter.

**Issue**: "No documents found"
- **Solution**: Check that `documents/` directory exists and contains supported files.

**Issue**: Slow processing
- **Solution**: Large PDFs can be slow. Consider splitting into smaller files or using RAG for very large documents.

**Issue**: Table extraction issues
- **Solution**: Some PDF tables are images. Docling works best with text-based tables.

## Examples

### Example 1: Academic Paper

```bash
python agent.py --file paper.pdf "Summarize the methodology"
```

### Example 2: Financial Analysis

```bash
python agent.py --file quarterly_report.xlsx "What were the expenses breakdown?"
```

### Example 3: Legal Document

```bash
python agent.py --file contract.docx "List all party obligations"
```

## Resources

- [Claude Agent SDK Docs](https://docs.claude.com/en/api/agent-sdk/python)
- [Docling Documentation](https://github.com/DS4SD/docling)
- [Original docling-rag-agent](../../docling-rag-agent/)

---

**Created by**: oTTomator Community
**License**: MIT
**Version**: 1.0.0
