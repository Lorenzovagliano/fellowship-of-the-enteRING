#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdfextractor.pipeline import ExtractionPipeline
from dotenv import load_dotenv

load_dotenv()


def extract_single(args):
    if not os.path.exists(args.pdf):
        print(f"Erro: PDF não encontrado: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    
    try:
        schema = json.loads(args.schema)
    except json.JSONDecodeError as e:
        print(f"Erro: Schema JSON inválido: {e}", file=sys.stderr)
        sys.exit(1)
    
    with open(args.pdf, 'rb') as f:
        pdf_content = f.read()
    
    pipeline = ExtractionPipeline()
    result, metadata = pipeline.extract(pdf_content, args.label, schema)
    
    output = {
        "data": result,
        "metadata": metadata
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def extract_batch(args):
    if not os.path.exists(args.dataset):
        print(f"Erro: Dataset não encontrado: {args.dataset}", file=sys.stderr)
        sys.exit(1)
    
    with open(args.dataset, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    if not isinstance(dataset, list):
        print("Erro: Dataset deve ser uma lista JSON", file=sys.stderr)
        sys.exit(1)
    
    requests = []
    for idx, item in enumerate(dataset, 1):
        if not all(k in item for k in ['label', 'extraction_schema', 'pdf_path']):
            print(f"Aviso: Item {idx} está incompleto, pulando...", file=sys.stderr)
            continue
        
        pdf_path = item['pdf_path']
        if args.pdf_dir:
            pdf_path = os.path.join(args.pdf_dir, pdf_path)
        
        if not os.path.exists(pdf_path):
            print(f"Aviso: PDF não encontrado: {pdf_path}, pulando...", file=sys.stderr)
            continue
        
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        requests.append({
            "pdf_content": pdf_content,
            "label": item['label'],
            "schema": item['extraction_schema'],
            "pdf_path": pdf_path,
        })
    
    if not requests:
        print("Erro: Nenhum item válido no dataset", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processando {len(requests)} documentos...", file=sys.stderr)
    
    pipeline = ExtractionPipeline()
    results = []
    
    for idx, req in enumerate(requests, 1):
        if args.verbose:
            print(f"[{idx}/{len(requests)}] Processando {os.path.basename(req['pdf_path'])}...", file=sys.stderr)
        
        result, metadata = pipeline.extract(
            pdf_content=req["pdf_content"],
            label=req["label"],
            schema=req["schema"]
        )
        
        results.append({
            "pdf_path": req["pdf_path"],
            "label": req["label"],
            "data": result,
            "metadata": metadata
        })
        
        if args.verbose:
            method = metadata.get("method", "unknown")
            time = metadata.get("processing_time", 0)
            print(f"  ✓ Método: {method}, Tempo: {time:.3f}s", file=sys.stderr)
    
    output = {
        "results": results,
        "total_processed": len(results)
    }
    
    if args.stats:
        output["statistics"] = pipeline.get_stats()
        
        if args.verbose:
            print("\n" + "="*70, file=sys.stderr)
            print("ESTATÍSTICAS", file=sys.stderr)
            print("="*70, file=sys.stderr)
            stats = pipeline.get_stats()
            print(f"Total extrações: {stats['extractions']['total']}", file=sys.stderr)
            print(f"Cache hits: {stats['extractions']['cache_hits']}", file=sys.stderr)
            print(f"Heurística apenas: {stats['extractions']['heuristic_only']}", file=sys.stderr)
            print(f"Híbrido (heur+LLM): {stats['extractions']['hybrid']}", file=sys.stderr)
            print(f"Tempo médio: {stats['performance']['avg_time']}s", file=sys.stderr)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\nResultados salvos em: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="PDF Extractor - Sistema inteligente de extração de dados",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a executar')
    
    extract_parser = subparsers.add_parser('extract', help='Extrair dados de um único PDF')
    extract_parser.add_argument('--label', required=True, help='Label do documento')
    extract_parser.add_argument('--schema', required=True, help='Schema JSON de campos')
    extract_parser.add_argument('--pdf', required=True, help='Caminho do PDF')
    extract_parser.add_argument('--pretty', action='store_true', help='Output JSON formatado')
    
    batch_parser = subparsers.add_parser('batch', help='Processar lote de PDFs')
    batch_parser.add_argument('--dataset', required=True, help='Arquivo dataset.json')
    batch_parser.add_argument('--pdf-dir', help='Diretório base dos PDFs (opcional)')
    batch_parser.add_argument('--output', '-o', help='Arquivo de saída (opcional)')
    batch_parser.add_argument('--stats', action='store_true', help='Incluir estatísticas')
    batch_parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    batch_parser.add_argument('--pretty', action='store_true', help='Output JSON formatado')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'extract':
            extract_single(args)
        elif args.command == 'batch':
            extract_batch(args)
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nErro fatal: {e}", file=sys.stderr)
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
