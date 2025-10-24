import logging
import tempfile
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from docling_service import DoclingVLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VLM Docling API",
    description="PDF parsing using GraniteDocling VLM with CUDA acceleration",
    version="1.0.0"
)

# Initialize the Docling VLM service (singleton)
docling_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global docling_service
    try:
        logger.info("Starting up VLM Docling API...")
        docling_service = DoclingVLMService()
        logger.info("VLM Docling service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize VLM service: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint - Hello World"""
    return {"message": "Hello World", "service": "VLM Docling API"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if docling_service and docling_service.is_ready():
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "service": "vlm-docling", "vlm_ready": True}
        )
    return JSONResponse(
        status_code=503,
        content={"status": "unhealthy", "service": "vlm-docling", "vlm_ready": False}
    )


@app.get("/api/hello/{name}")
async def hello_name(name: str):
    """Personalized greeting"""
    return {"message": f"Hello, {name}!"}


@app.get("/api/parse-pdf/status")
async def parse_status() -> Dict:
    """
    Check if the PDF parsing service is ready
    Returns service status and GPU information
    """
    if not docling_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return docling_service.get_status()


@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)) -> Dict:
    """
    Parse a PDF file using GraniteDocling VLM
    
    Args:
        file: PDF file to parse
        
    Returns:
        JSON structure containing the parsed document
    """
    if not docling_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not docling_service.is_ready():
        raise HTTPException(status_code=503, detail="VLM service not ready")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create temporary file to store upload
    temp_file = None
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Parse the PDF
        result = docling_service.parse_pdf(temp_path)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Parsing failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "filename": file.filename,
            "status": "success",
            "document": result.get("document"),
            "metadata": result.get("metadata")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file and Path(temp_path).exists():
            try:
                Path(temp_path).unlink()
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.error(f"Failed to delete temporary file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

