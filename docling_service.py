import logging
from pathlib import Path
from typing import Union, Dict

import torch

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline

# VLM Pipeline imports
from docling.datamodel.pipeline_options import VlmPipelineOptions, AcceleratorOptions
from docling.datamodel import vlm_model_specs

logger = logging.getLogger(__name__)

class DoclingVLMService:
    """Basic VLM service for parsing PDFs using VLM pipeline."""
    
    def __init__(self):
        logger.info("Initializing Docling VLM Service...")
        self.converter = self._create_converter()
        logger.info("Docling VLM Service ready")

    def _create_converter(self) -> DocumentConverter:
        # Use GraniteDocling model for Linux/CUDA (TRANSFORMERS backend)
        # For Mac, use GRANITEDOCLING_MLX instead
        model = vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
        
        # Configure GPU acceleration for H200
        accelerator_options = AcceleratorOptions(
            num_threads=4,
            device="cuda"
        )
        
        # Log VLM configuration
        logger.info("=" * 60)
        logger.info("Configuring VLM Pipeline...")
        logger.info(f"Model: {model.repo_id}")
        logger.info(f"Backend: {model.backend}")
        logger.info(f"Accelerator: {accelerator_options.device}")
        logger.info("=" * 60)
        
        # Create VLM pipeline options - pass model spec directly
        vlm_pipeline_options = VlmPipelineOptions(
            vlm_options=model,
            accelerator_options=accelerator_options,
            generate_page_images=True,
            generate_picture_images=False,
            images_scale=2.0,
            do_picture_description=True,
        )

        converter = DocumentConverter(
            format_options = {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls = VlmPipeline,
                    pipeline_options = vlm_pipeline_options
                )
            }
        )
        
        # Debug: Print converter type
        print(f"DEBUG: Converter type: {type(converter)}")
        # Note: Pipeline and VLM model types will be visible during first conversion
        # Inside the pipeline: print(type(self.vlm_model))
        
        logger.info("✓ VLM Pipeline initialized successfully")
        logger.info("=" * 60)
        return converter

    def parse_pdf(self, file_path: Union[str, Path]) -> Dict:
        logger.info(f"Parsing PDF: {file_path}")
        try:
            result = self.converter.convert(str(file_path))
            
            # Debug: Log VLM model type after pipeline initialization
            try:
                initialized_pipelines = self.converter._get_initialized_pipelines()
                if initialized_pipelines:
                    for cache_key, pipeline in initialized_pipelines.items():
                        logger.info(f"Pipeline class: {type(pipeline).__name__}")
                        if hasattr(pipeline, 'build_pipe') and pipeline.build_pipe:
                            vlm_wrapper = pipeline.build_pipe[0]
                            logger.info(f"VLM wrapper class: {type(vlm_wrapper).__name__}")
                            if hasattr(vlm_wrapper, 'vlm_model'):
                                model = vlm_wrapper.vlm_model
                                logger.info(f"Model class loaded: {type(model).__name__}")
                                if type(model).__name__ == 'Idefics3Model':
                                    logger.warning("⚠️  ISSUE IDENTIFIED: Model is Idefics3Model instead of expected model!")
            except Exception as debug_err:
                logger.debug(f"Debug inspection failed: {debug_err}")
            
            doc_dict = result.document.export_to_dict()
            logger.info(f"Successfully parsed: {file_path}")
            return {"success": True, "document": doc_dict}
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            return {"success": False, "error": str(e)}