import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from docling_service import DoclingVLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Docling VLM API",
    description="Basic PDF parsing with Docling VLM pipeline",
    version="1.0.0"
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
    
    Upload a PDF and get the parsed document structure
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

