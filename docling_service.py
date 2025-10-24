"""
Docling VLM Service - PDF parsing using GraniteDocling VLM
Handles all document parsing logic with CUDA acceleration
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Union
import torch

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, VlmPipelineOptions
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend

logger = logging.getLogger(__name__)


class DoclingVLMService:
    """
    Singleton service for parsing PDFs using GraniteDocling VLM
    Optimized for H200 GPU with CUDA 12.6.2
    """
    
    _instance: Optional['DoclingVLMService'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DoclingVLMService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the VLM service with GraniteDocling model"""
        if not self._initialized:
            logger.info("Initializing DoclingVLMService...")
            self._setup_device()
            self._initialize_converter()
            self._initialized = True
            logger.info("DoclingVLMService initialized successfully")
    
    def _setup_device(self):
        """Setup CUDA device for GPU acceleration"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda":
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
            logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA version: {torch.version.cuda}")
        else:
            logger.warning("CUDA not available, using CPU")
    
    def _initialize_converter(self):
        """Initialize DocumentConverter with VLM pipeline"""
        try:
            # Configure VLM pipeline options
            vlm_options = VlmPipelineOptions()
            
            # Configure PDF pipeline with VLM
            pipeline_options = PdfPipelineOptions(
                vlm_options=vlm_options
            )
            pipeline_options.do_table_structure = True
            pipeline_options.do_ocr = True
            
            # Initialize DocumentConverter with VLM backend
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                        backend=DoclingParseDocumentBackend
                    )
                }
            )
            
            logger.info("DocumentConverter initialized with VLM pipeline")
            
        except Exception as e:
            logger.error(f"Failed to initialize converter: {str(e)}")
            raise
    
    def parse_pdf(self, file_path: Union[str, Path]) -> Dict:
        """
        Parse a PDF file using GraniteDocling VLM
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing the parsed document structure
            
        Raises:
            Exception: If parsing fails
        """
        try:
            logger.info(f"Starting PDF parsing: {file_path}")
            
            # Convert the document
            result = self.converter.convert(str(file_path))
            
            # Export to JSON structure
            doc_dict = result.document.export_to_dict()
            
            logger.info(f"Successfully parsed PDF: {file_path}")
            
            return {
                "success": True,
                "document": doc_dict,
                "metadata": {
                    "source": str(file_path),
                    "num_pages": len(doc_dict.get("pages", [])),
                    "device": self.device
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document": None
            }
    
    def is_ready(self) -> bool:
        """Check if the service is ready to process documents"""
        return self._initialized
    
    def get_status(self) -> Dict:
        """Get service status information"""
        return {
            "initialized": self._initialized,
            "device": self.device if hasattr(self, 'device') else "unknown",
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None
        }

