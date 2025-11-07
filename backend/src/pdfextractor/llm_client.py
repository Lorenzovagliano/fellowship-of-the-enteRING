import json
import os
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Defina a variável de ambiente ou crie arquivo .env"
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        
        self.stats = {
            "total_calls": 0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
        }
    
    def extract_fields(
        self,
        text: str,
        schema: Dict[str, str],
        label: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, any]:
        max_length = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
        if len(text) > max_length:
            text = text[:max_length] + "\n... (texto truncado)"
        
        prompt = self._build_prompt(text, schema, label, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente de extração de dados. "
                            "Extraia informações do texto e retorne APENAS JSON válido. "
                            "Se um campo não existir no texto, retorne null."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                reasoning_effort="minimal",
            )
            
            usage = response.usage
            self.stats["total_calls"] += 1
            self.stats["total_tokens_input"] += usage.prompt_tokens
            self.stats["total_tokens_output"] += usage.completion_tokens
            
            result = json.loads(response.choices[0].message.content)
            
            for field in schema.keys():
                if field not in result:
                    result[field] = None
            
            return result
            
        except Exception as e:
            print(f"Erro ao chamar LLM: {e}")
            return {field: None for field in schema.keys()}
    
    def _build_prompt(
        self,
        text: str,
        schema: Dict[str, str],
        label: Optional[str],
        context: Optional[Dict]
    ) -> str:
        label_ctx = f"\nTipo de documento: {label}\n" if label else ""
        
        context_ctx = ""
        if context:
            context_ctx = "\nCampos já identificados:\n"
            for k, v in context.items():
                if v is not None:
                    context_ctx += f"- {k}: {v}\n"
        
        schema_str = "\n".join([
            f'"{field}": {desc}'
            for field, desc in schema.items()
        ])
        
        prompt = f"""Extraia os seguintes campos deste texto.{label_ctx}{context_ctx}

Campos para extrair:
{schema_str}

Texto:
{text}

Retorne JSON com os campos. Se um campo não existir, use null."""
        
        return prompt
    
    def get_stats(self) -> Dict:
        return {
            "calls": self.stats["total_calls"],
            "tokens": {
                "input": self.stats["total_tokens_input"],
                "output": self.stats["total_tokens_output"],
                "total": self.stats["total_tokens_input"] + self.stats["total_tokens_output"]
            }
        }
