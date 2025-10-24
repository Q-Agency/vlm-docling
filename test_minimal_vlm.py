#!/usr/bin/env python3
"""
Minimal test script for Granite Docling VLM PDF parsing.

This demonstrates the simplest working configuration for VLM-based PDF parsing.
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ultra_minimal():
    """
    Ultra-minimal example: uses all default settings.
    GraniteDocling with Transformers backend is the default.
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.pipeline.vlm_pipeline import VlmPipeline
    
    logger.info("=" * 80)
    logger.info("TEST 1: Ultra-Minimal Configuration (All Defaults)")
    logger.info("=" * 80)
    
    # Simplest possible configuration
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
            ),
        }
    )
    
    # Test with a sample PDF (you can replace this with your own)
    test_pdf = "https://arxiv.org/pdf/2408.09869"  # Docling paper
    
    logger.info(f"Converting: {test_pdf}")
    result = converter.convert(test_pdf)
    
    # Export to markdown
    markdown = result.document.export_to_markdown()
    
    logger.info(f"✓ Success! Converted {len(result.document.pages)} pages")
    logger.info(f"First 500 chars of output:\n{markdown[:500]}...")
    
    return result


def test_with_cuda():
    """
    Minimal example with CUDA acceleration for H200.
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.pipeline.vlm_pipeline import VlmPipeline
    from docling.datamodel.pipeline_options import VlmPipelineOptions, AcceleratorOptions
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Minimal Configuration with CUDA Acceleration")
    logger.info("=" * 80)
    
    # Configure for CUDA
    pipeline_options = VlmPipelineOptions(
        accelerator_options=AcceleratorOptions(
            device="cuda",
            num_threads=4,
        )
    )
    
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options
            ),
        }
    )
    
    # Test with a smaller PDF for faster testing
    test_pdf = "https://arxiv.org/pdf/2408.09869"
    
    logger.info(f"Converting with CUDA: {test_pdf}")
    result = converter.convert(test_pdf)
    
    # Export to different formats
    markdown = result.document.export_to_markdown()
    doc_dict = result.document.export_to_dict()
    
    logger.info(f"✓ Success! Converted {len(result.document.pages)} pages")
    logger.info(f"Document has {len(doc_dict.get('texts', []))} text elements")
    
    return result


def test_with_service_class():
    """
    Test using the DoclingVLMService class.
    """
    from docling_service import DoclingVLMService
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Using DoclingVLMService Class")
    logger.info("=" * 80)
    
    # Initialize service
    service = DoclingVLMService()
    
    # Parse a PDF
    test_pdf = "https://arxiv.org/pdf/2408.09869"
    result = service.parse_pdf(test_pdf)
    
    if result["success"]:
        logger.info(f"✓ Success! Parsed {result['num_pages']} pages")
        logger.info(f"Document keys: {list(result['document'].keys())}")
    else:
        logger.error(f"✗ Failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    try:
        # Run tests
        logger.info("Starting VLM Pipeline Tests...")
        
        # Test 1: Ultra-minimal (commented out by default - uncomment to run)
        # test_ultra_minimal()
        
        # Test 2: With CUDA acceleration (commented out by default - uncomment to run)
        # test_with_cuda()
        
        # Test 3: Using the service class
        test_with_service_class()
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ All tests completed successfully!")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Test failed with error: {e}", exc_info=True)
        sys.exit(1)

