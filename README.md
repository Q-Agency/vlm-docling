# VLM Docling - PDF Parsing with GraniteDocling

FastAPI application for parsing PDF documents using GraniteDocling VLM with CUDA acceleration on H200 GPU.

## Features

- 🚀 FastAPI REST API for PDF parsing
- 🔥 GraniteDocling VLM (IBM Granite 3.1 8B Instruct) for advanced PDF understanding
- 🎯 CUDA 12.6.2 acceleration optimized for H200 GPU
- 📄 JSON document structure output
- 🐳 Docker containerization with GPU support
- 📊 Swagger UI for easy testing

## Requirements

### Hardware
- NVIDIA H200 GPU (or compatible GPU)
- Ubuntu with NVIDIA drivers installed
- NVIDIA Container Toolkit

### Software
- Docker with NVIDIA runtime support
- Docker Compose

## Installation

1. **Verify NVIDIA Container Toolkit:**
```bash
docker run --rm --gpus all nvidia/cuda:12.6.2-base-ubuntu22.04 nvidia-smi
```

2. **Clone and build:**
```bash
git clone <your-repo-url>
cd vlm-docling
./refresh.sh
```

## Usage

### Starting the Service

```bash
# Build and start with GPU support
docker compose up -d

# Or use the refresh script
./refresh.sh

# View logs
docker compose logs -f q-structurize
```

### API Endpoints

The service runs on `http://localhost:8879` and provides the following endpoints:

#### 1. Health Check
```bash
curl http://localhost:8879/health
```

#### 2. VLM Service Status
```bash
curl http://localhost:8879/api/parse-pdf/status
```

Returns GPU information and service readiness.

#### 3. Parse PDF
Upload a PDF file for parsing:

```bash
curl -X POST "http://localhost:8879/api/parse-pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

Or use Swagger UI at: `http://localhost:8879/docs`

### Using Swagger UI

1. Navigate to `http://localhost:8879/docs`
2. Click on the `/api/parse-pdf` endpoint
3. Click "Try it out"
4. Upload a PDF file
5. Click "Execute"
6. View the parsed JSON document structure

### Standalone Script

For testing outside Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Parse a PDF
python example_vlm_parse.py document.pdf output

# Parse from URL
python example_vlm_parse.py https://arxiv.org/pdf/2408.09869 output
```

This will create `output.json` and `output.md` files.

## API Response Format

```json
{
  "filename": "document.pdf",
  "status": "success",
  "document": {
    "pages": [...],
    "content": [...],
    "tables": [...],
    "figures": [...]
  },
  "metadata": {
    "source": "/tmp/uploaded.pdf",
    "num_pages": 10,
    "device": "cuda"
  }
}
```

## Architecture

- **main.py** - FastAPI application with HTTP endpoints
- **docling_service.py** - Core PDF parsing logic with VLM
- **Dockerfile** - CUDA 12.6.2 enabled container
- **docker-compose.yml** - GPU configuration and orchestration
- **example_vlm_parse.py** - Standalone testing script

## Configuration

### GPU Settings

Modify `docker-compose.yml` to adjust GPU settings:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1  # Number of GPUs
          capabilities: [gpu]
```

### Model Caching

Models are cached in a Docker volume to avoid re-downloading:

```yaml
volumes:
  - huggingface-cache:/app/.cache/huggingface
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.6.2-base-ubuntu22.04 nvidia-smi

# Install NVIDIA Container Toolkit if needed
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Service Not Starting

```bash
# View logs
docker compose logs -f

# Check service status
curl http://localhost:8879/api/parse-pdf/status
```

### Out of Memory

Reduce model size or increase GPU memory allocation.

## Development

### Refresh and Rebuild

```bash
# Full rebuild without cache
./refresh.sh --no-cache

# Without git pull
./refresh.sh --no-pull

# View logs in foreground
./refresh.sh --foreground
```

### Push Changes

```bash
./gitpush.sh
```

## Technical Details

- **Base Image**: nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04
- **Python**: 3.11
- **Docling**: 2.58.0
- **PyTorch**: 2.5.1 with CUDA 12.4 support
- **VLM Model**: IBM Granite 3.1 8B Instruct

## References

- [Docling Documentation](https://docling-project.github.io/docling/)
- [GraniteDocling VLM Example](https://docling-project.github.io/docling/examples/minimal_vlm_pipeline/)
- [Docling GitHub](https://github.com/docling-project/docling)

## License

MIT
