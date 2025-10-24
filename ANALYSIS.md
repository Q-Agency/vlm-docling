# Docling VLM Analysis Report

## Current Code Issues

### Problems Identified in `docling_service.py`:

1. **Invalid Parameter**: `do_picture_description=True` (line 51)
   - This parameter does NOT exist in `VlmPipelineOptions`
   - Not found in the class definition or any parent classes

2. **Redundant Parameter**: `images_scale=2.0` (line 50)
   - While this IS a valid parameter from `PaginatedPipelineOptions`
   - The model spec `GRANITEDOCLING_TRANSFORMERS` already has `scale=2.0` built-in
   - Setting it here is redundant and may cause confusion

3. **Over-configuration**: The code is trying to configure too many parameters
   - The minimal working example from docling reference shows much simpler setup
   - Many parameters have good defaults

## Correct Structure from Docling Reference

### VlmPipelineOptions Valid Parameters:
```python
class VlmPipelineOptions(PaginatedPipelineOptions):
    generate_page_images: bool = True  # default
    force_backend_text: bool = False   # default
    vlm_options: Union[InlineVlmOptions, ApiVlmOptions] = GRANITEDOCLING_TRANSFORMERS  # default
```

### AcceleratorOptions Valid Parameters:
```python
class AcceleratorOptions(BaseSettings):
    num_threads: int = 4
    device: Union[str, AcceleratorDevice] = "auto"
    cuda_use_flash_attention2: bool = False
```

### GRANITEDOCLING_TRANSFORMERS Model Spec:
```python
GRANITEDOCLING_TRANSFORMERS = InlineVlmOptions(
    repo_id="ibm-granite/granite-docling-258M",
    prompt="Convert this page to docling.",
    response_format=ResponseFormat.DOCTAGS,
    inference_framework=InferenceFramework.TRANSFORMERS,
    transformers_model_type=TransformersModelType.AUTOMODEL_IMAGETEXTTOTEXT,
    supported_devices=[AcceleratorDevice.CPU, AcceleratorDevice.CUDA],
    extra_generation_config=dict(skip_special_tokens=False),
    scale=2.0,  # ← Already configured here!
    temperature=0.0,
    max_new_tokens=8192,
    stop_strings=["</doctag>", "<|end_of_text|>"],
)
```

## Minimal Working Implementation

### Option 1: Ultra-Minimal (Use all defaults)
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
        ),
    }
)
```

### Option 2: Minimal with CUDA acceleration
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.pipeline_options import VlmPipelineOptions, AcceleratorOptions

pipeline_options = VlmPipelineOptions(
    accelerator_options=AcceleratorOptions(
        device="cuda",
        num_threads=4
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
```

### Option 3: Custom model with specific settings
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.pipeline_options import VlmPipelineOptions, AcceleratorOptions
from docling.datamodel import vlm_model_specs

pipeline_options = VlmPipelineOptions(
    vlm_options=vlm_model_specs.GRANITEDOCLING_TRANSFORMERS,
    accelerator_options=AcceleratorOptions(
        device="cuda",
        num_threads=4,
        cuda_use_flash_attention2=False
    ),
    generate_page_images=True,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=pipeline_options
        ),
    }
)
```

## Recommendations

1. **Remove invalid parameters** from `VlmPipelineOptions`:
   - Remove: `do_picture_description`
   - Remove: `images_scale` (redundant)
   - Remove: `generate_picture_images` (only needed for specific use cases)

2. **Simplify the configuration**:
   - Start with minimal working example
   - Add parameters only when needed
   - Use model spec defaults (they're already optimized)

3. **For H200 CUDA acceleration**:
   - Only need to set `device="cuda"` in AcceleratorOptions
   - Consider `cuda_use_flash_attention2=True` for better performance
   - `num_threads` can stay at default (4)

4. **Testing approach**:
   - Start with ultra-minimal version first
   - Verify it works before adding any custom options
   - Add accelerator options only after basic functionality works

