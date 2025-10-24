#!/usr/bin/env python3
"""
Example script for parsing PDFs using GraniteDocling VLM
This script can be run standalone for testing purposes

Usage:
    python example_vlm_parse.py <path_to_pdf>
    python example_vlm_parse.py https://arxiv.org/pdf/2408.09869
"""

import sys
import json
import logging
from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, VlmPipelineOptions
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_pdf_with_vlm(pdf_source: str, output_file: str = None):
    """
    Parse a PDF using GraniteDocling VLM
    
    Args:
        pdf_source: Path to PDF file or URL
        output_file: Optional output file path for JSON results
    """
    logger.info(f"Parsing PDF: {pdf_source}")
    
    try:
        # Configure VLM pipeline
        vlm_options = VlmPipelineOptions()
        
        pipeline_options = PdfPipelineOptions(
            vlm_options=vlm_options
        )
        pipeline_options.do_table_structure = True
        pipeline_options.do_ocr = True
        
        # Initialize converter with VLM backend
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=DoclingParseDocumentBackend
                )
            }
        )
        
        logger.info("DocumentConverter initialized with VLM pipeline")
        
        # Convert the document
        logger.info("Starting conversion...")
        result = converter.convert(pdf_source)
        
        # Export to dictionary
        doc_dict = result.document.export_to_dict()
        
        # Print summary
        logger.info("=" * 80)
        logger.info("PDF PARSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Source: {pdf_source}")
        logger.info(f"Number of pages: {len(doc_dict.get('pages', []))}")
        
        # Print Markdown preview (first 500 chars)
        markdown = result.document.export_to_markdown()
        logger.info("\nMarkdown Preview (first 500 chars):")
        logger.info("-" * 80)
        logger.info(markdown[:500] + "..." if len(markdown) > 500 else markdown)
        logger.info("-" * 80)
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            
            # Save JSON
            json_path = output_path.with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(doc_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"\n✓ JSON saved to: {json_path}")
            
            # Save Markdown
            md_path = output_path.with_suffix('.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            logger.info(f"✓ Markdown saved to: {md_path}")
        
        return doc_dict
        
    except Exception as e:
        logger.error(f"Error parsing PDF: {str(e)}")
        raise


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python example_vlm_parse.py <path_to_pdf_or_url> [output_file]")
        print("\nExamples:")
        print("  python example_vlm_parse.py document.pdf")
        print("  python example_vlm_parse.py https://arxiv.org/pdf/2408.09869 output")
        sys.exit(1)
    
    pdf_source = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info("")
        
        parse_pdf_with_vlm(pdf_source, output_file)
        
    except Exception as e:
        logger.error(f"Failed to parse PDF: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

