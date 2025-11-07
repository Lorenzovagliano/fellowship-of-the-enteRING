import time
from typing import Optional, Dict, Any
from collections import OrderedDict
from diskcache import Cache
from .cache_key import CacheKeyGenerator


class CacheManager:
    
    def __init__(self, cache_dir: str = "./storage/cache_data", memory_size: int = 100):
        self.memory_cache: OrderedDict = OrderedDict()
        self.memory_size = memory_size
        
        self.disk_cache = Cache(
            cache_dir,
            size_limit=1024**3,
            eviction_policy='least-recently-used'
        )
        
        self.key_gen = CacheKeyGenerator()
        
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "total_requests": 0,
        }
    
    def get(
        self, 
        pdf_content: bytes,
        label: str, 
        schema: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        self.stats["total_requests"] += 1
        
        full_key = self.key_gen.generate_full_key(pdf_content, label, schema)
        
        if full_key in self.memory_cache:
            self.memory_cache.move_to_end(full_key)
            self.stats["l1_hits"] += 1
            result = self.memory_cache[full_key]
            result["_cache_level"] = "L1_MEMORY"
            return result
        
        disk_result = self.disk_cache.get(full_key)
        if disk_result is not None:
            self._add_to_l1(full_key, disk_result)
            self.stats["l2_hits"] += 1
            disk_result["_cache_level"] = "L2_DISK"
            return disk_result
        
        partial = self._try_partial_match(pdf_content, label, schema)
        if partial:
            self.stats["l3_hits"] += 1
            partial["_cache_level"] = "L3_PARTIAL"
            return partial
        
        self.stats["misses"] += 1
        return None
    
    def set(
        self,
        pdf_content: bytes,
        label: str,
        schema: Dict[str, str],
        result: Dict[str, Any]
    ):
        full_key = self.key_gen.generate_full_key(pdf_content, label, schema)
        
        clean_result = {k: v for k, v in result.items() if not k.startswith("_")}
        
        self._add_to_l1(full_key, clean_result)
        self.disk_cache.set(full_key, clean_result)
        
        for field_name, field_value in clean_result.items():
            if field_value is not None:
                field_key = self.key_gen.generate_field_key(pdf_content, label, field_name)
                self.disk_cache.set(field_key, {
                    "value": field_value,
                    "timestamp": time.time()
                })
    
    def _add_to_l1(self, key: str, value: Any):
        if len(self.memory_cache) >= self.memory_size:
            self.memory_cache.popitem(last=False)
        self.memory_cache[key] = value
    
    def _try_partial_match(
        self,
        pdf_content: bytes,
        label: str,
        schema: Dict[str, str]
    ) -> Optional[Dict]:
        result = {}
        found_count = 0
        
        for field_name in schema.keys():
            field_key = self.key_gen.generate_field_key(pdf_content, label, field_name)
            cached_field = self.disk_cache.get(field_key)
            
            if cached_field:
                result[field_name] = cached_field["value"]
                found_count += 1
            else:
                result[field_name] = None
        
        match_rate = found_count / len(schema) if schema else 0
        
        if match_rate >= 0.5:
            result["_partial_match_rate"] = match_rate
            result["_needs_llm_fields"] = [k for k, v in result.items() if v is None and not k.startswith("_")]
            return result
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        total = self.stats["total_requests"]
        total_hits = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]
        
        return {
            "requests": total,
            "hits": {
                "l1": self.stats["l1_hits"],
                "l2": self.stats["l2_hits"],
                "l3": self.stats["l3_hits"],
                "total": total_hits
            },
            "misses": self.stats["misses"],
            "hit_rate": f"{total_hits / max(1, total) * 100:.1f}%",
            "cache_sizes": {
                "memory_items": len(self.memory_cache),
                "disk_items": len(self.disk_cache)
            }
        }
