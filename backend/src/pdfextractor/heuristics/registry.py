import re
from typing import Dict, Any, Tuple


class HeuristicExtractor:
    
    PATTERNS = {
        'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
        'cnpj': r'\b\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}\b',
        'telefone': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
        'cep': r'\b\d{5}-?\d{3}\b',
        'email': r'[\w\.-]+@[\w\.-]+\.\w+',
        'data': r'\b\d{2}/\d{2}/\d{4}\b',
        'inscricao': r'\b\d{5,8}\b',
        'numero': r'\b\d+\b',
    }
    
    def extract_fields(
        self,
        text: str,
        schema: Dict[str, str],
        label: str
    ) -> Tuple[Dict[str, Any], Dict[str, float], bool]:
        results = {}
        confidence = {}
        
        if 'oab' in label.lower():
            results, confidence = self._extract_oab(text, schema)
        elif 'sistema' in label.lower():
            results, confidence = self._extract_sistema(text, schema)
        else:
            results, confidence = self._extract_generic(text, schema)
        
        needs_llm = any(
            results.get(field) is None or confidence.get(field, 0) < 0.75
            for field in schema.keys()
        )
        
        return results, confidence, needs_llm
    
    def _extract_oab(
        self,
        text: str,
        schema: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        results = {}
        confidence = {}
        
        for field_name in schema.keys():
            field_lower = field_name.lower()
            
            if 'nome' in field_lower:
                match = re.search(r'\b([A-ZÀ-Ú]+(?:[\s\'][A-ZÀ-Ú]+){1,4})\b', text)
                if match:
                    results[field_name] = match.group(1).strip()
                    confidence[field_name] = 0.9
            
            elif 'inscri' in field_lower:
                match = re.search(r'\b(\d{6})\b', text)
                if match:
                    results[field_name] = match.group(1)
                    confidence[field_name] = 0.95
            
            elif 'seccional' in field_lower:
                match = re.search(r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', text)
                if match:
                    results[field_name] = match.group(1)
                    confidence[field_name] = 0.9
            
            elif 'subsec' in field_lower or 'subseç' in field_lower:
                match = re.search(r'Conselho Seccional[\s\-]+(.+?)(?=\n|$)', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1).strip()
                    confidence[field_name] = 0.85
            
            elif 'categoria' in field_lower:
                match = re.search(r'\b(ADVOGAD[OA]|SUPLEMENTAR|ESTAGIÁRI[OA])\b', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1)
                    confidence[field_name] = 0.9
            
            elif 'telefone' in field_lower:
                match = re.search(self.PATTERNS['telefone'], text)
                if match:
                    results[field_name] = match.group(0)
                    confidence[field_name] = 0.85
            
            elif 'situa' in field_lower:
                match = re.search(r'Situação\s+(\w+)', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1)
                    confidence[field_name] = 0.9
            
            elif 'endereco' in field_lower or 'endereço' in field_lower:
                match = re.search(r'Endereço.+?\n(.+?\n.+?\n.+?)\n', text, re.IGNORECASE | re.DOTALL)
                if match:
                    results[field_name] = match.group(1).strip().replace('\n', ', ')
                    confidence[field_name] = 0.8
            
            if field_name not in results:
                results[field_name] = None
                confidence[field_name] = 0.0
        
        return results, confidence
    
    def _extract_sistema(
        self,
        text: str,
        schema: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        results = {}
        confidence = {}
        
        for field_name in schema.keys():
            field_lower = field_name.lower()
            
            if 'sistema' in field_lower and 'tipo' not in field_lower:
                patterns = [
                    r'\b(CONSIGNADO|CREDITO|FINANCIAMENTO|EMPRESTIMO)\b',
                    r'Sistema[:\s]+([A-Z]{5,}?)(?=\s|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        results[field_name] = match.group(1).strip()
                        confidence[field_name] = 0.85
                        break
            
            elif 'tipo' in field_lower and 'sistema' in field_lower:
                match = re.search(r'Tipo\s+(?:de\s+)?Sistema[:\s]+([A-Z\s]+)', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1).strip()
                    confidence[field_name] = 0.85
            
            elif 'produto' in field_lower:
                patterns = [
                    r'Produto[:\s]+([A-Z\s]+?)(?=\n|Sistema|Qtd)',
                    r'(?:Produto|PRODUTO)[:\s]*([A-Z]{5,})',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        results[field_name] = match.group(1).strip()
                        confidence[field_name] = 0.85
                        break
            
            elif 'cidade' in field_lower:
                match = re.search(r'Cidade[:\s]+([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)*)', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1).strip()
                    confidence[field_name] = 0.9
            
            elif 'qtd' in field_lower or 'quantidade' in field_lower or 'parcela' in field_lower:
                patterns = [
                    r'(?:Qtd|Quantidade|Parcelas)[:\s]+(\d+)',
                    r'(\d+)\s+parcelas?',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        results[field_name] = match.group(1)
                        confidence[field_name] = 0.95
                        break
            
            elif 'venc' in field_lower or 'vcto' in field_lower or 'vern' in field_lower:
                patterns = [
                    r'(?:Vcto\s+mais\s+antigo)[^\d]*(\d{2}/\d{2}/\d{4})',
                    r'(?:Vcto|Vencimento|venc)[^\d]{0,20}(\d{2}/\d{2}/\d{4})',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        results[field_name] = match.group(1)
                        confidence[field_name] = 0.95
                        break
            
            elif 'data' in field_lower:
                if 'base' in field_lower or 'ref' in field_lower:
                    match = re.search(r'Data\s+(?:Referência|Base)[:\s]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
                    if match:
                        results[field_name] = match.group(1)
                        confidence[field_name] = 0.95
                else:
                    match = re.search(self.PATTERNS['data'], text)
                    if match:
                        results[field_name] = match.group(0)
                        confidence[field_name] = 0.7
            
            elif 'valor' in field_lower or 'parc' in field_lower:
                patterns = [
                    r'(?:Vlr?\.?\s*Parc\.?|Valor|V/r)[:\s]*\n?\s*((?:\d{1,3}\.)*\d{1,3},\d{2})',
                    r'R?\$\s*((?:\d{1,3}\.)*\d{1,3},\d{2})',
                    r'\b((?:\d{1,3}\.)+\d{1,3},\d{2})\b',
                    r'\b(\d{1,3},\d{2})\b',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        valor_str = match.group(1)
                        valor_normalizado = valor_str.replace('.', '').replace(',', '.')
                        results[field_name] = valor_normalizado
                        confidence[field_name] = 0.9
                        break
            
            if field_name not in results:
                results[field_name] = None
                confidence[field_name] = 0.0
        
        return results, confidence
    
    def _extract_generic(
        self,
        text: str,
        schema: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        results = {}
        confidence = {}
        
        for field_name in schema.keys():
            field_lower = field_name.lower()
            
            for pattern_name, pattern in self.PATTERNS.items():
                if pattern_name in field_lower:
                    match = re.search(pattern, text)
                    if match:
                        results[field_name] = match.group(0)
                        confidence[field_name] = 0.7
                        break
            
            if field_name not in results:
                results[field_name] = None
                confidence[field_name] = 0.0
        
        return results, confidence
