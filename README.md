# Docling VLM - Basic PDF Parsing

Minimal FastAPI application for parsing PDF documents using Docling VLM pipeline with CUDA acceleration.

## Features

- 🚀 Minimal FastAPI REST API for PDF parsing
- 📄 Docling VLM pipeline for document understanding
- 🎯 CUDA 12.6.2 acceleration for H200 GPU
- 📊 JSON document structure output
- 🐳 Docker with GPU support
- 📖 Swagger UI at `/docs`

## Requirements

- NVIDIA GPU (H200 or compatible)
- Ubuntu with NVIDIA drivers
- NVIDIA Container Toolkit
- Docker & Docker Compose

## Quick Start

```bash
# Build and run
./refresh.sh

# Or manually
docker compose up -d
```

## Usage

### Starting the Service

```bash
# Build and start with GPU support
docker compose up -d

# Or use the refresh script
./refresh.sh

# View logs
docker compose logs -f vlm-docling
```

### API Endpoints

Service runs on `http://localhost:8879`

**Swagger UI:** `http://localhost:8879/docs`

**Endpoints:**
- `GET /` - Root
- `GET /health` - Health check
- `POST /api/parse-pdf` - Upload and parse PDF

### Usage

**Via Swagger UI:**
1. Open `http://localhost:8879/docs`
2. Try `/api/parse-pdf` endpoint
3. Upload PDF
4. View parsed JSON

**Via curl:**
```bash
curl -X POST "http://localhost:8879/api/parse-pdf" \
  -F "file=@document.pdf"
```

## Project Structure

```
main.py              # FastAPI app
docling_service.py   # VLM parsing service
Dockerfile           # CUDA 12.6.2 container
docker-compose.yml   # GPU configuration
requirements.txt     # Just docling[vlm] + FastAPI
```

## Development & Testing

### Running Tests

Test the minimal VLM implementation:

```bash
# Test with the service class
python test_minimal_vlm.py

# Or test individual examples in the script
```

### Code Analysis

See `ANALYSIS.md` for detailed analysis of:
- Proper VLM configuration structure
- Invalid parameters that were removed
- Minimal working implementation options
- Best practices for Granite Docling VLM

### Key Configuration Points

**Correct VLmPipelineOptions parameters:**
- `vlm_options`: Model specification (default: GRANITEDOCLING_TRANSFORMERS)
- `accelerator_options`: Device and threading configuration
- `generate_page_images`: Whether to generate page images (default: True)

**AcceleratorOptions for H200:**
```python
AcceleratorOptions(
    device="cuda",
    num_threads=4,
    cuda_use_flash_attention2=False  # or True for better performance
)
```

## Notes

- Models are cached in Docker volume `huggingface-cache`
- First run downloads VLM models (~500MB for Granite Docling 258M)
- VLM processing is slower but more accurate than standard pipelines
- Model scale (2.0) is pre-configured in GRANITEDOCLING_TRANSFORMERS spec
- The implementation uses minimal required parameters (most have good defaults)

## View Logs

```bash
docker compose logs -f vlm-docling
```

## References

- [Docling Documentation](https://docling-project.github.io/docling/)
- [Docling GitHub](https://github.com/docling-project/docling)
- [Granite Docling Model](https://huggingface.co/ibm-granite/granite-docling-258M)
- Local reference: `docling-reference/` (for development only, not tracked in git)
