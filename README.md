# Docling VLM - Basic PDF Parsing

Minimal FastAPI application for parsing PDF documents using Docling VLM pipeline with CUDA acceleration.

## Features

- 🚀 Minimal FastAPI REST API for PDF parsing
- 📄 Docling VLM pipeline for document understanding
- 🎯 CUDA 12.6.2 acceleration for H200 GPU
- 📊 JSON document structure output
- ✂️ **NEW:** Intelligent document chunking with HybridChunker
- 🔍 **NEW:** Curated metadata extraction for RAG/semantic search
- 📋 **NEW:** Table serialization for embeddings
- 🤖 **NEW:** Custom tokenizer support
- 🐳 Docker with GPU support
- 📖 Swagger UI at `/docs`

## Requirements

- NVIDIA GPU (H200 or compatible)
- Ubuntu with NVIDIA drivers
- NVIDIA Container Toolkit
- Docker & Docker Compose

## Quick Start

```bash
# Build and run
./refresh.sh

# Or manually
docker compose up -d
```

## Usage

### Starting the Service

```bash
# Build and start with GPU support
docker compose up -d

# Or use the refresh script
./refresh.sh

# View logs
docker compose logs -f vlm-docling
```

### API Endpoints

Service runs on `http://localhost:8879`

**Swagger UI:** `http://localhost:8879/docs`

**Endpoints:**
- `GET /` - Root
- `GET /health` - Health check
- `POST /api/parse-pdf` - Upload and parse PDF (returns full document JSON)
- `POST /api/parse-and-chunk` - Upload, parse, and chunk PDF for RAG/search

### Usage

**Via Swagger UI:**
1. Open `http://localhost:8879/docs`
2. Try `/api/parse-pdf` endpoint
3. Upload PDF
4. View parsed JSON

**Via curl:**

Parse only (get full document JSON):
```bash
curl -X POST "http://localhost:8879/api/parse-pdf" \
  -F "file=@document.pdf"
```

Parse and chunk (for RAG/semantic search):
```bash
# Basic chunking with defaults
curl -X POST "http://localhost:8879/api/parse-and-chunk" \
  -F "file=@document.pdf"

# Advanced: Custom chunk size and tokenizer
curl -X POST "http://localhost:8879/api/parse-and-chunk" \
  -F "file=@document.pdf" \
  -F "max_tokens=1024" \
  -F "merge_peers=true" \
  -F "model_name=sentence-transformers/all-MiniLM-L6-v2" \
  -F "serialize_tables=true"
```

## Project Structure

```
main.py              # FastAPI app with chunking endpoints
docling_service.py   # VLM parsing and chunking service
hybrid_chunker.py    # Document chunking with HybridChunker
tokenizer_manager.py # Tokenizer caching and management
table_serializer.py  # Table extraction and serialization
Dockerfile           # CUDA 12.6.2 container
docker-compose.yml   # GPU configuration
requirements.txt     # Dependencies (docling[vlm], transformers, FastAPI)
```

## Document Chunking

The service now includes intelligent document chunking for RAG and semantic search applications.

### Features

**HybridChunker Integration:**
- Preserves document structure (headings, sections, tables)
- Intelligent context preservation across chunks
- Configurable chunk size (max_tokens)
- Optional peer merging for better coherence

**Metadata Extraction:**
- `content_type`: Identifies text, table, list, or heading chunks
- `heading_path`: Full breadcrumb of section headings (e.g., "Chapter 1 > Section 2")
- `pages`: List of page numbers where chunk content appears
- `doc_items_count`: Number of document items in the chunk

**Table Serialization:**
- Converts tables to key-value format for embeddings
- Format: "Column1: Value1, Column2: Value2, ..."
- Includes table captions
- Optimized for semantic search

**Custom Tokenizers:**
- Use any HuggingFace tokenizer model
- Automatic caching (LRU cache for up to 10 tokenizers)
- Falls back to HybridChunker's built-in tokenizer if not specified

### Chunking Parameters

- `max_tokens` (default: 512): Maximum tokens per chunk
- `merge_peers` (default: true): Merge undersized successive chunks with same headings
- `model_name` (optional): HuggingFace model for custom tokenizer
- `serialize_tables` (default: false): Enable table serialization

### Example Output

```json
{
  "filename": "research_paper.pdf",
  "num_pages": 15,
  "chunks": [
    {
      "text": "search_document: Introduction\n\nThis paper presents...",
      "section_title": "Introduction",
      "chunk_index": 0,
      "metadata": {
        "content_type": "text",
        "heading_path": "Abstract > Introduction",
        "pages": [1, 2],
        "doc_items_count": 8
      }
    },
    {
      "text": "search_document: Results\n\nTable: Experimental Results\nMetric: Accuracy, Value: 95.2%\nMetric: F1-Score, Value: 93.8%",
      "section_title": "Results",
      "chunk_index": 5,
      "metadata": {
        "content_type": "table",
        "heading_path": "Results > Experimental Evaluation",
        "pages": [8],
        "doc_items_count": 1,
        "has_table_structure": true
      }
    }
  ]
}
```

## Development & Testing

### Running Tests

Test the minimal VLM implementation:

```bash
# Test with the service class
python test_minimal_vlm.py

# Or test individual examples in the script
```

### Code Analysis

See `ANALYSIS.md` for detailed analysis of:
- Proper VLM configuration structure
- Invalid parameters that were removed
- Minimal working implementation options
- Best practices for Granite Docling VLM

### Key Configuration Points

**Correct VLmPipelineOptions parameters:**
- `vlm_options`: Model specification (default: GRANITEDOCLING_TRANSFORMERS)
- `accelerator_options`: Device and threading configuration
- `generate_page_images`: Whether to generate page images (default: True)

**AcceleratorOptions for H200:**
```python
AcceleratorOptions(
    device="cuda",
    num_threads=4,
    cuda_use_flash_attention2=False  # or True for better performance
)
```

## Notes

- Models are cached in Docker volume `huggingface-cache`
- First run downloads VLM models (~500MB for Granite Docling 258M)
- VLM processing is slower but more accurate than standard pipelines
- Model scale (2.0) is pre-configured in GRANITEDOCLING_TRANSFORMERS spec
- The implementation uses minimal required parameters (most have good defaults)

## View Logs

```bash
docker compose logs -f vlm-docling
```

## References

- [Docling Documentation](https://docling-project.github.io/docling/)
- [Docling GitHub](https://github.com/docling-project/docling)
- [Granite Docling Model](https://huggingface.co/ibm-granite/granite-docling-258M)
- Local reference: `docling-reference/` (for development only, not tracked in git)
