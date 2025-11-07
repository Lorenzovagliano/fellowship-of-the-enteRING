import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class LLMSettings:
    model: str
    temperature: float
    max_tokens: int
    reasoning_effort: str
    cost_input_per_token: float
    cost_output_per_token: float


@dataclass
class CacheSettings:
    directory: str
    memory_size: int
    disk_size_gb: int


@dataclass
class HeuristicSettings:
    confidence_threshold: float
    position_x_tolerance: int
    position_y_tolerance: int


@dataclass
class LimitSettings:
    max_pdf_size_mb: int
    max_schema_fields: int
    max_text_length: int


class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        self.llm = LLMSettings(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "minimal"),
            cost_input_per_token=0.150 / 1_000_000,
            cost_output_per_token=0.600 / 1_000_000
        )
        
        self.cache = CacheSettings(
            directory=os.getenv("CACHE_DIR", "./storage/cache_data"),
            memory_size=int(os.getenv("CACHE_L1_SIZE", "100")),
            disk_size_gb=int(os.getenv("CACHE_L2_SIZE_GB", "1"))
        )
        
        self.heuristics = HeuristicSettings(
            confidence_threshold=float(os.getenv("HEURISTIC_CONFIDENCE_THRESHOLD", "0.75")),
            position_x_tolerance=int(os.getenv("POSITION_X_TOLERANCE", "30")),
            position_y_tolerance=int(os.getenv("POSITION_Y_TOLERANCE", "20"))
        )
        
        self.limits = LimitSettings(
            max_pdf_size_mb=int(os.getenv("MAX_PDF_SIZE_MB", "10")),
            max_schema_fields=int(os.getenv("MAX_SCHEMA_FIELDS", "50")),
            max_text_length=int(os.getenv("MAX_TEXT_LENGTH", "10000"))
        )
    
    def validate(self) -> bool:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm": {
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "reasoning_effort": self.llm.reasoning_effort,
            },
            "cache": {
                "directory": self.cache.directory,
                "memory_size": self.cache.memory_size,
                "disk_size_gb": self.cache.disk_size_gb,
            },
            "heuristics": {
                "confidence_threshold": self.heuristics.confidence_threshold,
            },
            "limits": {
                "max_pdf_size_mb": self.limits.max_pdf_size_mb,
                "max_schema_fields": self.limits.max_schema_fields,
                "max_text_length": self.limits.max_text_length,
            },
        }


settings = Settings()
