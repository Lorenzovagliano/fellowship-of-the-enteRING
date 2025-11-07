import io
import pdfplumber
from typing import Optional, List, Dict, Any
from functools import lru_cache


def extract_text_from_pdf(pdf_content: bytes) -> Optional[str]:
    try:
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                return None
            
            page = pdf.pages[0]
            text = page.extract_text()
            
            return text if text else None
            
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
        return None


def extract_text_with_coords(pdf_content: bytes) -> List[Dict[str, Any]]:
    try:
        pdf_file = io.BytesIO(pdf_content)
        elements = []
        
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                return []
            
            page = pdf.pages[0]
            
            words = page.extract_words()
            
            for word in words:
                elements.append({
                    'text': word['text'].strip(),
                    'x0': round(word['x0'], 1),
                    'y0': round(word['y0'], 1),
                    'x1': round(word['x1'], 1),
                    'y1': round(word['y1'], 1),
                    'type': 'word',
                })
            
            return elements
            
    except Exception as e:
        print(f"Erro ao extrair coordenadas do PDF: {e}")
        return []


@lru_cache(maxsize=100)
def extract_text_from_pdf_cached(pdf_hash: str, pdf_content: bytes) -> Optional[str]:
    return extract_text_from_pdf(pdf_content)


def group_words_by_line(elements: List[Dict[str, Any]], y_tolerance: int = 4) -> List[List[Dict]]:
    if not elements:
        return []
    
    sorted_elements = sorted(elements, key=lambda e: (e['y0'], e['x0']))
    
    lines = []
    current_line = [sorted_elements[0]]
    current_y = sorted_elements[0]['y0']
    
    for elem in sorted_elements[1:]:
        if abs(elem['y0'] - current_y) <= y_tolerance:
            current_line.append(elem)
        else:
            lines.append(current_line)
            current_line = [elem]
            current_y = elem['y0']
    
    if current_line:
        lines.append(current_line)
    
    return lines


def extract_tables(pdf_content: bytes) -> List[List[List[str]]]:
    try:
        pdf_file = io.BytesIO(pdf_content)
        tables = []
        
        with pdfplumber.open(pdf_file) as pdf:
            page = pdf.pages[0]
            extracted_tables = page.extract_tables()
            
            if extracted_tables:
                tables = extracted_tables
        
        return tables
        
    except Exception:
        return []
