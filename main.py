import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from docling_service import DoclingVLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Docling VLM API",
    description="PDF parsing and chunking with Docling VLM pipeline. Parse PDFs with VLM for accurate document understanding, then optionally chunk documents for RAG and semantic search applications.",
    version="1.1.0"
)

# Global service instance
docling_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize VLM service on startup"""
    global docling_service
    docling_service = DoclingVLMService()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Docling VLM API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy" if docling_service else "initializing"}


@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """
    Parse a PDF file using VLM pipeline
    
    Upload a PDF and get the parsed document structure in full JSON format.
    
    Returns:
        - filename: Original filename
        - document: Full DoclingDocument as dictionary
    """
    if not docling_service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    
    # Save uploaded file temporarily
    temp_path = None
    try:
        contents = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        # Parse with VLM
        result = docling_service.parse_pdf(temp_path)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "filename": file.filename,
            "document": result.get("document")
        }
        
    finally:
        # Cleanup
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()


@app.post("/api/parse-and-chunk")
async def parse_and_chunk(
    file: UploadFile = File(...),
    max_tokens: int = Form(512, description="Maximum tokens per chunk"),
    merge_peers: bool = Form(True, description="Merge undersized successive chunks with same headings"),
    model_name: Optional[str] = Form(None, description="Optional HuggingFace model name for custom tokenizer (e.g., 'sentence-transformers/all-MiniLM-L6-v2')"),
    serialize_tables: bool = Form(False, description="Serialize table chunks as key-value pairs for embeddings")
):
    """
    Parse a PDF file using VLM pipeline and chunk it for RAG/semantic search
    
    This endpoint performs the full pipeline:
    1. Parse PDF with VLM for accurate document understanding
    2. Chunk the document into smaller pieces with intelligent context preservation
    3. Extract curated metadata for each chunk (content_type, heading_path, pages, etc.)
    
    Parameters:
        - file: PDF file to process
        - max_tokens: Maximum tokens per chunk (default: 512)
        - merge_peers: Whether to merge undersized successive chunks (default: true)
        - model_name: Optional custom tokenizer model (default: uses HybridChunker's built-in)
        - serialize_tables: Format table chunks as key-value pairs (default: false)
    
    Returns:
        - filename: Original filename
        - num_pages: Number of pages in the document
        - chunks: Array of chunks, each containing:
            - text: Chunk text (prefixed with "search_document: ")
            - section_title: Most specific heading for the chunk
            - chunk_index: Index of the chunk (0-based)
            - metadata: Curated metadata (content_type, heading_path, pages, doc_items_count)
    
    Example Response:
    ```json
    {
        "filename": "document.pdf",
        "num_pages": 10,
        "chunks": [
            {
                "text": "search_document: Introduction\\n\\nThis document describes...",
                "section_title": "Introduction",
                "chunk_index": 0,
                "metadata": {
                    "content_type": "text",
                    "heading_path": "Chapter 1 > Introduction",
                    "pages": [1, 2],
                    "doc_items_count": 5
                }
            }
        ]
    }
    ```
    """
    if not docling_service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    
    # Save uploaded file temporarily
    temp_path = None
    try:
        contents = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        # Parse with VLM
        logger.info(f"Parsing PDF: {file.filename}")
        result = docling_service.parse_pdf(temp_path)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # Get the ConversionResult object (not the dict)
        # We need to re-parse to get the actual DoclingDocument object
        logger.info(f"Re-converting to get DoclingDocument object for chunking")
        conversion_result = docling_service.converter.convert(temp_path)
        document = conversion_result.document
        
        # Chunk the document
        logger.info(f"Chunking document with max_tokens={max_tokens}, merge_peers={merge_peers}")
        chunks = docling_service.chunk_document(
            document=document,
            max_tokens=max_tokens,
            merge_peers=merge_peers,
            model_name=model_name,
            serialize_tables=serialize_tables
        )
        
        return {
            "filename": file.filename,
            "num_pages": result.get("num_pages"),
            "chunks": chunks
        }
        
    finally:
        # Cleanup
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

