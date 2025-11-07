import xxhash
import json
from typing import Dict


class CacheKeyGenerator:
    
    @staticmethod
    def hash_pdf(pdf_content: bytes) -> str:
        return xxhash.xxh64(pdf_content).hexdigest()
    
    @staticmethod
    def hash_schema(schema: Dict[str, str]) -> str:
        schema_json = json.dumps(schema, sort_keys=True)
        return xxhash.xxh64(schema_json.encode()).hexdigest()
    
    @staticmethod
    def generate_full_key(pdf_content: bytes, label: str, schema: Dict[str, str]) -> str:
        pdf_hash = CacheKeyGenerator.hash_pdf(pdf_content)
        schema_hash = CacheKeyGenerator.hash_schema(schema)
        return f"{pdf_hash}:{label}:{schema_hash}"
    
    @staticmethod
    def generate_field_key(pdf_content: bytes, label: str, field_name: str) -> str:
        pdf_hash = CacheKeyGenerator.hash_pdf(pdf_content)
        return f"{pdf_hash}:{label}:field:{field_name}"
    
    @staticmethod
    def generate_template_key(label: str) -> str:
        return f"template:{label}"
