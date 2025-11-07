from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class DocumentLabel(BaseModel):
    label: str = Field(..., description="Document type identifier")
    extraction_schema: Dict[str, str] = Field(..., description="Mapping of field names to descriptions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "invoice",
                "extraction_schema": {
                    "invoice_number": "número da nota fiscal",
                    "total_amount": "valor total"
                }
            }
        }


class ProcessingMetadata(BaseModel):
    method: str = Field(..., description="Extraction method: cache, heuristic, hybrid, empty")
    processing_time: float = Field(..., description="Processing time in seconds")
    heuristic_confidence: Optional[Dict[str, float]] = Field(default=None)
    cache_level: Optional[str] = Field(default=None)


class ExtractionResult(BaseModel):
    data: Dict[str, Any] = Field(..., description="Extracted values")
    metadata: ProcessingMetadata


class BatchItem(BaseModel):
    index: int
    data: Dict[str, Any]
    metadata: ProcessingMetadata


class BatchResult(BaseModel):
    results: List[BatchItem]
    total_processed: int


class PipelineStatistics(BaseModel):
    extractions: Dict[str, int]
    performance: Dict[str, float]
    llm: Dict[str, Any]
    cache: Optional[Dict[str, Any]] = Field(default=None)


class HealthStatus(BaseModel):
    status: str
    version: str
