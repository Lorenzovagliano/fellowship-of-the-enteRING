import time
from typing import Dict, Any, Tuple
from .pdf_parser import extract_text_from_pdf as extract_text
from .cache import Cache
from .heuristics import Heuristics
from .llm_client import LLMClient


class ExtractionPipeline:
    
    def __init__(
        self,
        cache_dir: str = "./storage/cache_data",
        enable_cache: bool = True,
        enable_heuristics: bool = True
    ):
        self.cache = Cache(cache_dir=cache_dir) if enable_cache else None
        self.heuristics = Heuristics() if enable_heuristics else None
        self.llm = LLMClient()
        
        self.stats = {
            "total_extractions": 0,
            "cache_hits": 0,
            "heuristic_only": 0,
            "hybrid": 0,
            "llm_only": 0,
            "total_time": 0.0,
        }
    
    def extract(
        self,
        pdf_content: bytes,
        label: str,
        schema: Dict[str, str],
        use_cache: bool = True
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        start_time = time.time()
        self.stats["total_extractions"] += 1
        
        if use_cache and self.cache:
            cached = self.cache.get(pdf_content, label, schema)
            if cached:
                self.stats["cache_hits"] += 1
                
                elapsed = time.time() - start_time
                
                metadata = {
                    "method": "cache",
                    "cache_level": cached.get("_cache_level", "unknown"),
                    "processing_time": elapsed,
                }
                
                result = {k: v for k, v in cached.items() if not k.startswith("_")}
                
                return result, metadata
        
        text = extract_text(pdf_content)
        
        if not text or len(text.strip()) < 10:
            result = {field: None for field in schema}
            metadata = {
                "method": "empty",
                "processing_time": time.time() - start_time,
            }
            return result, metadata
        
        heuristic_result = {}
        confidence_scores = {}
        needs_llm = True
        
        if self.heuristics:
            heuristic_result, confidence_scores, needs_llm = self.heuristics.extract_fields(
                text, schema, label
            )
        
        if not needs_llm:
            final_result = heuristic_result
            method = "heuristic"
            self.stats["heuristic_only"] += 1
        else:
            missing_fields = {
                k: v for k, v in schema.items()
                if heuristic_result.get(k) is None or confidence_scores.get(k, 0) < 0.75
            }
            
            if missing_fields:
                llm_result = self.llm.extract_fields(
                    text=text,
                    schema=missing_fields,
                    label=label,
                    context=heuristic_result
                )
                
                final_result = {**heuristic_result, **llm_result}
                method = "hybrid"
                self.stats["hybrid"] += 1
            else:
                final_result = heuristic_result
                method = "heuristic"
                self.stats["heuristic_only"] += 1
        
        if use_cache and self.cache:
            self.cache.set(pdf_content, label, schema, final_result)
        
        elapsed = time.time() - start_time
        self.stats["total_time"] += elapsed
        
        metadata = {
            "method": method,
            "processing_time": elapsed,
            "heuristic_confidence": {
                k: round(v, 2) for k, v in confidence_scores.items()
            } if confidence_scores else {},
        }
        
        return final_result, metadata
    
    def process(self, pdf_content: bytes, label: str, schema: Dict[str, str], use_cache: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return self.extract(pdf_content, label, schema, use_cache=use_cache)
    
    def get_stats(self) -> Dict[str, Any]:
        total = self.stats["total_extractions"]
        
        stats = {
            "extractions": {
                "total": total,
                "cache_hits": self.stats["cache_hits"],
                "heuristic_only": self.stats["heuristic_only"],
                "hybrid": self.stats["hybrid"],
                "llm_only": self.stats["llm_only"],
            },
            "performance": {
                "total_time": round(self.stats["total_time"], 2),
                "avg_time": round(self.stats["total_time"] / max(1, total), 3),
            },
            "llm": self.llm.get_stats(),
        }
        
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        return self.get_stats()
    
    def reset_statistics(self):
        self.stats = {
            "total_extractions": 0,
            "cache_hits": 0,
            "heuristic_only": 0,
            "hybrid": 0,
            "llm_only": 0,
            "total_time": 0.0,
        }


Pipeline = ExtractionPipeline
