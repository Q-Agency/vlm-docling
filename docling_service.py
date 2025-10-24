"""
Docling VLM Service - PDF parsing using GraniteDocling VLM
"""

import logging
from pathlib import Path
from typing import Dict, Union

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel import vlm_model_specs
from docling.datamodel.pipeline_options import VlmPipelineOptions, PdfPipelineOptions
from docling.pipeline.vlm_pipeline import VlmPipeline

logger = logging.getLogger(__name__)


class DoclingVLMService:
    """VLM service using GraniteDocling model for PDF parsing"""
    
    def __init__(self):
        """Initialize the VLM service with GraniteDocling"""
        logger.info("Initializing Docling VLM Service...")
        self.converter = self._create_converter()
        logger.info("GraniteDocling VLM Service ready")
    
    def _create_converter(self) -> DocumentConverter:
        """Create DocumentConverter with GraniteDocling VLM"""
        logger.info("=" * 60)
        logger.info("Configuring GraniteDocling VLM...")
        logger.info("Model: ibm-granite/granite-docling-258M")
        logger.info("Backend: transformers")
        logger.info("=" * 60)
        
        # Explicitly use GraniteDocling model with Transformers backend
        pipeline_options = PdfPipelineOptions(
            vlm_options=vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
        )
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                ),
            }
        )
        
        logger.info("✓ GraniteDocling VLM initialized")
        logger.info("=" * 60)
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

