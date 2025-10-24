from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="VLM Docling API",
    description="FastAPI Hello World",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint - Hello World"""
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "vlm-docling"}
    )


@app.get("/api/hello/{name}")
async def hello_name(name: str):
    """Personalized greeting"""
    return {"message": f"Hello, {name}!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

