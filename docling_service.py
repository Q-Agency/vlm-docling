"""
Docling VLM Service - Basic PDF parsing using Docling VLM pipeline
"""

import logging
from pathlib import Path
from typing import Dict, Union

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline

logger = logging.getLogger(__name__)


class DoclingVLMService:
    """Basic VLM service for parsing PDFs"""
    
    def __init__(self):
        """Initialize the VLM service"""
        logger.info("Initializing Docling VLM Service...")
        self.converter = self._create_converter()
        logger.info("Docling VLM Service ready")
    
    def _create_converter(self) -> DocumentConverter:
        """Create DocumentConverter with VLM pipeline"""
        # Most basic VLM pipeline setup
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                ),
            }
        )
        logger.info("VlmPipeline initialized")
        return converter
    
    def parse_pdf(self, file_path: Union[str, Path]) -> Dict:
        """
        Parse a PDF file using VLM pipeline
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with parsed document
        """
        try:
            logger.info(f"Parsing PDF: {file_path}")
            
            # Convert document
            result = self.converter.convert(str(file_path))
            
            # Export to dict
            doc_dict = result.document.export_to_dict()
            
            logger.info(f"Successfully parsed: {file_path}")
            
            return {
                "success": True,
                "document": doc_dict
            }
            
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

