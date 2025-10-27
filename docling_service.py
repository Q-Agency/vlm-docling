import logging
from pathlib import Path
from typing import Union, Dict, List, Any, Optional

import torch

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline

# VLM Pipeline imports
from docling.datamodel.pipeline_options import VlmPipelineOptions, AcceleratorOptions
from docling.datamodel import vlm_model_specs

# Chunking imports
from hybrid_chunker import chunk_document
from tokenizer_manager import get_tokenizer_manager

logger = logging.getLogger(__name__)

class DoclingVLMService:
    """Basic VLM service for parsing PDFs using VLM pipeline."""
    
    def __init__(self):
        logger.info("Initializing Docling VLM Service...")
        self.converter = self._create_converter()
        logger.info("Docling VLM Service ready")
        self._pipeline_verified = False

    def _create_converter(self) -> DocumentConverter:
        """
        Create a minimal working DocumentConverter with VLM pipeline.
        
        Uses GraniteDocling model with vLLM backend for 2-4x faster inference.
        For Mac, change to vlm_model_specs.GRANITEDOCLING_MLX.
        """
        # Select model based on platform - using vLLM for 2-4x faster inference
        model = vlm_model_specs.GRANITEDOCLING_VLLM.model_copy()
        
        # Optimize vLLM for H200 GPU (141GB HBM3e)
        model.extra_generation_config.update({
            "gpu_memory_utilization": 0.2,  # Use 70% of H200's 141GB (vs default 30%)
            "enforce_eager": True,  # Skip torch.compile (avoids C compiler requirement)
            "max_num_batched_tokens": 65536,  # Double batch size for better throughput
            "kv_cache_dtype": "auto",  # Optimize KV cache format
        })
        
        # Configure GPU acceleration for H200
        accelerator_options = AcceleratorOptions(
            device="cuda",
            num_threads=32,
            cuda_use_flash_attention2=False  # Not needed with vLLM
        )
        
        # Log VLM configuration
        logger.info("=" * 60)
        logger.info("Configuring VLM Pipeline...")
        logger.info(f"Model: {model.repo_id}")
        logger.info(f"Inference Framework: {model.inference_framework}")
        logger.info(f"Response Format: {model.response_format}")
        logger.info(f"Accelerator Device: {accelerator_options.device}")
        logger.info(f"Model Scale: {model.scale}")
        logger.info(f"Max Tokens: {model.max_new_tokens}")
        logger.info(f"Temperature: {model.temperature}")
        logger.info("=" * 60)
        
        # Create VLM pipeline options with minimal required parameters
        # Note: Most parameters have good defaults, only override what's needed
        vlm_pipeline_options = VlmPipelineOptions(
            vlm_options=model,
            accelerator_options=accelerator_options,
        )

        # Create converter with VLM pipeline
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=vlm_pipeline_options
                )
            }
        )
        
        logger.info("✓ VLM Pipeline initialized successfully")
        logger.info("=" * 60)
        return converter

    def _verify_model_loaded(self):
        """Verify the actual model being used (runs after first conversion)."""
        if self._pipeline_verified:
            return
            
        try:
            pipelines = self.converter._get_initialized_pipelines()
            
            for cache_key, pipeline in pipelines.items():
                logger.info("=" * 60)
                logger.info("🔍 MODEL VERIFICATION:")
                logger.info(f"  Pipeline Type: {type(pipeline).__name__}")
                
                if hasattr(pipeline, 'build_pipe') and pipeline.build_pipe:
                    vlm_wrapper = pipeline.build_pipe[0]
                    logger.info(f"  VLM Wrapper: {type(vlm_wrapper).__name__}")
                    
                    if hasattr(vlm_wrapper, 'vlm_options'):
                        opts = vlm_wrapper.vlm_options
                        logger.info(f"  ✅ Model Repository: {opts.repo_id}")
                        logger.info(f"  ✅ Inference Framework: {opts.inference_framework}")
                        logger.info(f"  ✅ Response Format: {opts.response_format}")
                        
                        # Verify it's Granite Docling
                        if "granite-docling" in opts.repo_id.lower():
                            logger.info("  ✅ CONFIRMED: Using Granite Docling VLM")
                        else:
                            logger.warning(f"  ⚠️  WARNING: Not Granite Docling! Using: {opts.repo_id}")
                    
                    if hasattr(vlm_wrapper, 'vlm_model'):
                        model = vlm_wrapper.vlm_model
                        logger.info(f"  ✅ Model Class: {type(model).__name__}")
                        
                        # Get device info
                        try:
                            device = next(model.parameters()).device
                            logger.info(f"  ✅ Running on Device: {device}")
                            
                            # Get model size
                            total_params = sum(p.numel() for p in model.parameters())
                            logger.info(f"  ✅ Model Parameters: {total_params:,} ({total_params/1e6:.1f}M)")
                        except:
                            pass
                        
                logger.info("=" * 60)
                
            self._pipeline_verified = True
        except Exception as e:
            logger.debug(f"Model verification failed: {e}")

    def parse_pdf(self, file_path: Union[str, Path]) -> Dict:
        """
        Parse a PDF file using the VLM pipeline.
        
        Args:
            file_path: Path to the PDF file (local path or URL)
            
        Returns:
            Dict with success status and either document data or error message
        """
        logger.info(f"Parsing PDF: {file_path}")
        try:
            # Convert the PDF using VLM pipeline
            result = self.converter.convert(str(file_path))
            
            # Verify model after first conversion (when it's actually loaded)
            self._verify_model_loaded()
            
            # Export to dictionary format
            doc_dict = result.document.export_to_dict()
            
            logger.info(f"✓ Successfully parsed: {file_path}")
            logger.info(f"  Pages: {len(result.document.pages)}")
            
            return {
                "success": True,
                "document": doc_dict,
                "num_pages": len(result.document.pages)
            }
        except Exception as e:
            logger.error(f"✗ Parse error: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def chunk_document(
        self,
        document,
        max_tokens: int = 512,
        merge_peers: bool = True,
        model_name: Optional[str] = None,
        serialize_tables: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Chunk a DoclingDocument into smaller pieces with metadata.
        
        Args:
            document: DoclingDocument object (from parse result)
            max_tokens: Maximum tokens per chunk (default: 512)
            merge_peers: Whether to merge undersized successive chunks (default: True)
            model_name: Optional HuggingFace model name for custom tokenizer
            serialize_tables: Whether to serialize table chunks (default: False)
            
        Returns:
            List of chunk dictionaries with text, section_title, chunk_index, and metadata
        """
        logger.info(f"Chunking document: max_tokens={max_tokens}, merge_peers={merge_peers}, model_name={model_name}")
        
        # Get tokenizer if model_name is provided
        tokenizer = None
        if model_name:
            try:
                tokenizer_manager = get_tokenizer_manager()
                tokenizer = tokenizer_manager.get_tokenizer(model_name)
                logger.info(f"Using custom tokenizer: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load tokenizer '{model_name}': {e}. Using default.")
        
        # Call the chunking function
        chunks = chunk_document(
            document=document,
            max_tokens=max_tokens,
            merge_peers=merge_peers,
            tokenizer=tokenizer,
            include_full_metadata=False,  # Use curated metadata only
            serialize_tables=serialize_tables
        )
        
        logger.info(f"✓ Document chunked into {len(chunks)} chunks")
        return chunks