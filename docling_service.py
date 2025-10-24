import logging
from pathlib import Path
from typing import Union, Dict

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline

# Updated imports
from docling.datamodel.pipeline_options_vlm_model import InlineVlmOptions, ResponseFormat, InferenceFramework
from docling.datamodel import vlm_model_specs

logger = logging.getLogger(__name__)

class DoclingVLMService:
    """Basic VLM service for parsing PDFs using VLM pipeline."""
    
    def __init__(self):
        logger.info("Initializing Docling VLM Service...")
        self.converter = self._create_converter()
        logger.info("Docling VLM Service ready")

    def _create_converter(self) -> DocumentConverter:
        # Choose the GraniteDocling model explicitly
        vlm_options = InlineVlmOptions(
            repo_id = vlm_model_specs.GRANITEDOCLING_TRANSFORMERS.repo_id,
            response_format = ResponseFormat.DOCTAGS,
            inference_framework = InferenceFramework.TRANSFORMERS,
            prompt = "Convert this page to DocTags markup.",
            scale = 2.0,
            temperature = 0.0,
        )
        logger.info(f"Using VLM model repo_id: {vlm_options.repo_id}")

        converter = DocumentConverter(
            format_options = {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls = VlmPipeline,
                    pipeline_options = {"vlm_options": vlm_options}
                )
            }
        )
        logger.info("VlmPipeline initialized")
        return converter

    def parse_pdf(self, file_path: Union[str, Path]) -> Dict:
        logger.info(f"Parsing PDF: {file_path}")
        try:
            result = self.converter.convert(str(file_path))
            doc_dict = result.document.export_to_dict()
            logger.info(f"Successfully parsed: {file_path}")
            return {"success": True, "document": doc_dict}
        except Exception as e:
            logger.error(f"Parse error: {str(e)}")
            return {"success": False, "error": str(e)}