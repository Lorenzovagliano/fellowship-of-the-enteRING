from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
from dotenv import load_dotenv

from .models import (
    ExtractionResult,
    DocumentLabel,
    BatchResult,
    BatchItem,
    PipelineStatistics,
    HealthStatus,
    ProcessingMetadata
)
from .pipeline import Pipeline
from .settings import settings
from . import __version__

load_dotenv()

app = FastAPI(
    title="PDF Extractor API",
    description="Intelligent PDF data extraction with heuristics, caching, and LLM fallback",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = Pipeline(
    cache_dir=settings.cache.directory,
    enable_cache=True,
    enable_heuristics=True
)


def validate_pdf_extension(filename: str) -> None:
    if not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")


def parse_schema(schema_str: str) -> dict:
    try:
        schema_dict = json.loads(schema_str)
        if not isinstance(schema_dict, dict):
            raise ValueError("Schema must be a JSON object")
        return schema_dict
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON schema: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def read_pdf_content(pdf: UploadFile) -> bytes:
    try:
        content = await pdf.read()
        max_size = settings.limits.max_pdf_size_mb * 1024 * 1024
        
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"PDF too large. Maximum size: {settings.limits.max_pdf_size_mb}MB"
            )
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")


@app.get("/", response_model=HealthStatus)
async def root():
    return HealthStatus(status="healthy", version=__version__)


@app.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="healthy", version=__version__)


@app.post("/extract", response_model=ExtractionResult)
async def extract_from_pdf(
    pdf: UploadFile = File(...),
    label: str = Form(...),
    schema: str = Form(...),
    use_cache: bool = Form(True)
):
    print(f"[EXTRACT] Received request:")
    print(f"  - PDF filename: {pdf.filename}")
    print(f"  - Label: {label}")
    print(f"  - Schema: {schema}")
    print(f"  - Use cache: {use_cache}")
    
    validate_pdf_extension(pdf.filename)
    schema_dict = parse_schema(schema)
    pdf_content = await read_pdf_content(pdf)
    
    print(f"  - PDF size: {len(pdf_content)} bytes")
    
    try:
        data, metadata = pipeline.process(pdf_content, label, schema_dict, use_cache=use_cache)
        print(f"  - Extraction successful, method: {metadata.get('method')}")
        return ExtractionResult(
            data=data,
            metadata=ProcessingMetadata(**metadata)
        )
    except Exception as e:
        print(f"  - Extraction error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


@app.post("/extract/batch", response_model=BatchResult)
async def extract_batch_from_pdfs(
    pdfs: List[UploadFile] = File(...),
    requests: str = Form(...),
    use_cache: bool = Form(True)
):
    try:
        requests_list = json.loads(requests)
        if not isinstance(requests_list, list):
            raise ValueError("Requests must be a JSON array")
        
        validated_requests = [DocumentLabel(**req) for req in requests_list]
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if len(pdfs) != len(validated_requests):
        raise HTTPException(
            status_code=400,
            detail=f"PDF count ({len(pdfs)}) must match request count ({len(validated_requests)})"
        )
    
    results = []
    
    for idx, (pdf, req) in enumerate(zip(pdfs, validated_requests)):
        validate_pdf_extension(pdf.filename)
        
        try:
            pdf_content = await read_pdf_content(pdf)
            data, metadata = pipeline.process(
                pdf_content,
                req.label,
                req.extraction_schema,
                use_cache=use_cache
            )
            
            results.append(BatchItem(
                index=idx,
                data=data,
                metadata=ProcessingMetadata(**metadata)
            ))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file {idx} ('{pdf.filename}'): {str(e)}"
            )
    
    return BatchResult(
        results=results,
        total_processed=len(results)
    )


@app.get("/stats", response_model=PipelineStatistics)
async def get_statistics():
    try:
        stats = pipeline.get_statistics()
        return PipelineStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.post("/stats/reset")
async def reset_statistics():
    try:
        pipeline.reset_statistics()
        return {"message": "Statistics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting stats: {str(e)}")

