# PDF Extractor

Sistema inteligente de extração de dados estruturados de arquivos PDF com otimização de custos e performance através de cache multinível e heurísticas.

*Interface desenvolvida com Lovable*

<img width="1398" height="778" alt="image" src="https://github.com/user-attachments/assets/b464994e-b44d-494d-912b-e3b8d7c44685" />


## Objetivo

Extrair informações estruturadas de arquivos PDF de forma **síncrona**, com **melhor custo-benefício** e **acurácia** possível, atendendo aos seguintes requisitos:

- Responder cada requisição em menos de 10 segundos
- Minimizar custos monetários de execução
- Garantir consistência e precisão das entidades extraídas
- Capacidade de acumular conhecimento a cada solicitação

## Início Rápido

### Pré-requisitos

- Docker e Docker Compose
- Chave de API da OpenAI

### Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd pdfextractor2
```

2. Configure a chave da API:
```bash
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

3. Inicie os serviços:
```bash
./start.sh
```

### Acessando a Aplicação

- **Frontend**: http://localhost:8080
- **API Backend**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs

### Uso via Interface Web

1. Acesse http://localhost:8080
2. Defina o **label** do documento (ex: "invoice", "oab", "sistema")
3. Cole o **schema JSON** com os campos a extrair
4. Faça upload do arquivo PDF
5. Clique em "Extrair Dados"

Exemplo de Input válido na UI:
- Label:
```
carteira_oab
```
- Schema:
```
{"nome":"Nome do profissional, normalmente no canto superior esquerdo da imagem","inscricao":"Número de inscrição do profissional","seccional":"Seccional do profissional","subsecao":"Subseção da qual o profissional faz parte","categoria":"Categoria, pode ser ADVOGADO, ADVOGADA, SUPLEMENTAR, ESTAGIÁRIO ou ESTAGIÁRIA","endereco_profissional":"Endereço do profissional","telefone_profissional":"Telefone do profissional","situacao":"Situação do profissional, normalmente no canto inferior direito."}
```

### Uso via API REST

#### Extração de documento único

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "pdf=@backend/examples/oab_1.pdf" \
  -F "label=carteira_oab" \
  -F 'schema={"nome":"Nome do profissional, normalmente no canto superior esquerdo da imagem","inscricao":"Número de inscrição do profissional","seccional":"Seccional do profissional","subsecao":"Subseção da qual o profissional faz parte","categoria":"Categoria, pode ser ADVOGADO, ADVOGADA, SUPLEMENTAR, ESTAGIÁRIO ou ESTAGIÁRIA","endereco_profissional":"Endereço do profissional","telefone_profissional":"Telefone do profissional","situacao":"Situação do profissional, normalmente no canto inferior direito."}' \
  -F 'use_cache=false'
```

#### Extração em batch (múltiplos documentos)

Para processar vários PDFs de uma só vez, use o endpoint `/extract/batch`:

Use um arquivo como esse `requests.json`:

```bash
[
  {
    "label": "carteira_oab",
    "extraction_schema": {
      "nome": "Nome do profissional",
      "inscricao": "Número de inscrição",
      "seccional": "Seccional do profissional"
    }
  },
  {
    "label": "invoice",
    "extraction_schema": {
      "total": "Valor total",
      "data": "Data do documento",
      "numero": "Número da fatura"
    }
  }
]
```

Faça a requisição batch (PDFs devem estar na mesma ordem das requisições)
```bash
curl -X POST "http://localhost:8000/extract/batch" \
  -F "pdfs=@backend/examples/oab_1.pdf" \
  -F "pdfs=@backend/examples/invoice.pdf" \
  -F "requests=$(cat requests.json)" \
  -F "use_cache=true"
```

**Resposta esperada:**
```json
{
  "results": [
    {
      "index": 0,
      "data": { "nome": "...", "inscricao": "...", "seccional": "..." },
      "metadata": { "method": "hybrid", "processing_time": 1.23 }
    },
    {
      "index": 1,
      "data": { "total": "...", "data": "...", "numero": "..." },
      "metadata": { "method": "cache", "processing_time": 0.01 }
    }
  ],
  "total_processed": 2
}
```


### Uso Local via CLI

Para desenvolvimento ou processamento em batch sem a necessidade da API REST, você pode executar o backend diretamente via linha de comando.

#### Configuração do Ambiente Local

Dependência: `Poetry`

1. **Navegue até o diretório do backend**:
```bash
cd backend
```

2. **Configure as variáveis de ambiente**:
```bash
# Crie um arquivo .env no diretório backend
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

3. **Instale as dependências**

```bash
poetry install
poetry shell
```

#### Comandos CLI Disponíveis

**Extração de documento único**:
```bash
python -m pdfextractor.cli extract \
  --pdf examples/oab_1.pdf \
  --label carteira_oab \
  --schema '{"nome":"Nome do profissional","inscricao":"Número de inscrição","seccional":"Seccional"}'
```

**Processamento em batch**:
```bash
# Usando o dataset de exemplo
python -m pdfextractor.cli batch \
  --dataset examples/dataset.json \
  --stats \
  --verbose

# Salvando resultados em arquivo
python -m pdfextractor.cli batch \
  --dataset examples/dataset.json \
  --output results.json \
  --stats \
  --verbose

**Formato do arquivo dataset.json**:
```json
[
  {
    "label": "carteira_oab",
    "extraction_schema": {
      "nome": "Nome do profissional",
      "inscricao": "Número de inscrição",
      "seccional": "Seccional do profissional"
    },
    "pdf_path": "examples/oab_1.pdf"
  },
  {
    "label": "invoice",
    "extraction_schema": {
      "total": "Valor total",
      "data": "Data do documento"
    },
    "pdf_path": "examples/invoice.pdf"
  }
]
```


## Arquitetura

### Visão Geral

O sistema implementa um **pipeline de extração em três estágios** com estratégia de fallback progressivo:

```
PDF → Cache → Heurísticas → LLM → Resultado
```

### Fluxo de Dados

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ POST /extract
       ▼
┌─────────────────────────────────────────────┐
│           API FastAPI (api.py)              │
│  - Validação (tamanho, formato, schema)     │
│  - Parsing de parâmetros                    │
└──────────────────┬──────────────────────────┘
                   ▼
┌──────────────────────────────────────────────┐
│      Pipeline (pipeline.py)                  │
│                                              │
│  1. Cache.get(pdf, label, schema)            │
│     └─► L1 → L2 → L3                         │
│                                              │
│  2. extract_text(pdf) via pdfplumber         │
│                                              │
│  3. Heuristics.extract_fields()              │
│     └─► Regex patterns + confidence          │
│                                              │
│  4. LLM.extract_fields() ← apenas missing    │
│     └─► OpenAI API (gpt-5-mini)              │
│                                              │
│  5. Cache.set(result)                        │
│     └─► L1 + L2 + campos individuais         │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│   Resultado + Metadata              │
│   {                                 │
│     "data": {...},                  │
│     "metadata": {                   │
│       "method": "hybrid",           │
│       "processing_time": 1.2,       │
│       "heuristic_confidence": {...} │
│     }                               │
│   }                                 │
└─────────────────────────────────────┘
```

## Desafios e Soluções

### Desafio 1: Latência e Custo de APIs LLM

**Contexto**: Cada chamada à API da OpenAI adiciona latência (1-5s) e custo monetário ($0.150 por milhão de tokens de entrada, $0.600 por milhão de tokens de saída). Com milhares de documentos, isso se torna insustentável tanto em tempo quanto em custo.

**Solução Implementada: Cache Multinível Inteligente**

Desenvolvemos um sistema de cache com três níveis progressivos que elimina redundâncias:

1. **L1 - Cache em Memória (RAM)**
   - OrderedDict com política LRU
   - Capacidade: 100 documentos mais recentes
   - Latência: ~0.001s (hit instantâneo)
   - Uso: Requisições repetidas em curto espaço de tempo

2. **L2 - Cache em Disco Persistente**
   - DiskCache com 1GB de espaço
   - Persiste entre reinicializações do serviço
   - Latência: ~0.01s (leitura de disco)
   - Uso: Documentos processados anteriormente

3. **L3 - Cache Parcial por Campo**
   - Armazena valores individuais de campos por (PDF hash + label + campo)
   - Permite reaproveitamento mesmo quando o schema muda
   - Match threshold: 50% dos campos
   - Uso: Documentos similares com schemas diferentes

**Estratégia de chaves**: Utilizamos xxHash64 (hash ultra-rápido) para identificar PDFs de forma única, combinado com o label e hash do schema. Isso permite:
- Identificação instantânea de duplicatas exatas
- Reutilização de campos já extraídos
- Redução de 80-95% nas chamadas LLM em datasets com documentos recorrentes

**Resultado**: Redução significativa de custos e latência através da reutilização de resultados previamente processados.

### Desafio 2: Acurácia vs Performance para Documentos Estruturados

**Contexto**: Documentos como carteiras da OAB, faturas e extratos financeiros possuem formato padronizado e campos em posições previsíveis. Usar LLM para extrair dados simples como CPF, número de inscrição ou valores monetários é um desperdício de recursos e introduz latência desnecessária.

**Solução Implementada: Motor de Heurísticas Especializadas**

Criamos extratores baseados em regex e análise estrutural que processam instantaneamente padrões conhecidos:

**Arquitetura do Motor**:

1. **Sistema de Registro por Tipo de Documento**
   - Detecta tipo via label ("oab", "sistema", etc.)
   - Seleciona extrator especializado
   - Fallback para extrator genérico

2. **Padrões Regex Otimizados**
   ```python
   # Exemplos de padrões implementados:
   CPF: r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
   CNPJ: r'\b\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}\b'
   Data: r'\b\d{2}/\d{2}/\d{4}\b'
   Telefone: r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}'
   ```

3. **Análise Contextual**
   - Para documentos OAB: busca "Situação Ativa", "Categoria ADVOGADO", estados brasileiros
   - Para documentos financeiros: extração de valores monetários, quantidade de parcelas, datas de vencimento
   - Contexto posicional: "Nome" geralmente está no topo, "Situação" no rodapé

4. **Sistema de Confiança**
   - Cada campo extraído recebe score de 0.0 a 1.0
   - Threshold configurável (padrão: 0.75)
   - Campos com baixa confiança são enviados para LLM
   - Campos com alta confiança evitam processamento adicional

**Estratégia Híbrida**:

O pipeline decide automaticamente a melhor abordagem:

```python
# Extração por heurística
heuristic_result, confidence_scores, needs_llm = heuristics.extract_fields(text, schema, label)

# Se confiança alta em todos os campos: usa apenas heurística
if not needs_llm:
    return heuristic_result  # método: "heuristic"

# Se alguns campos falharam: LLM apenas para campos faltantes
missing_fields = {k: v for k, v in schema.items() 
                 if result.get(k) is None or confidence.get(k, 0) < 0.75}
llm_result = llm.extract_fields(text, missing_fields, context=heuristic_result)
final = {**heuristic_result, **llm_result}  # método: "hybrid"
```

**Resultado**: Processamento instantâneo de documentos estruturados através de regex patterns, com fallback inteligente para LLM apenas quando necessário. O sistema híbrido otimiza custos sem sacrificar acurácia.

## Tecnologias

### Backend
- **Python 3.9+**
- **FastAPI**: Framework web assíncrono
- **pdfplumber**: Extração de texto e estrutura de PDFs
- **OpenAI API**: Processamento de linguagem natural
- **diskcache**: Persistência de cache em disco
- **xxhash**: Hashing ultra-rápido para chaves de cache
- **Pydantic**: Validação de dados e schemas

### Frontend
- **React + TypeScript**
- **Vite**: Build tool
- **TailwindCSS**: Estilização
- **shadcn/ui**: Componentes UI

### Infraestrutura
- **Docker + Docker Compose**: Containerização
- **uvicorn**: Servidor ASGI para FastAPI

## Estrutura do Projeto

```
pdfextractor2/
├── backend/
│   ├── src/pdfextractor/
│   │   ├── api.py              # Endpoints FastAPI
│   │   ├── pipeline.py         # Orquestração da extração
│   │   ├── pdf_parser.py       # Extração de texto (pdfplumber)
│   │   ├── llm_client.py       # Cliente OpenAI
│   │   ├── models.py           # Modelos Pydantic
│   │   ├── settings.py         # Configurações
│   │   ├── cli.py              # Interface de linha de comando
│   │   ├── cache/
│   │   │   ├── cache_manager.py   # Cache L1/L2/L3
│   │   │   └── cache_key.py       # Geração de chaves
│   │   └── heuristics/
│   │       └── registry.py        # Extratores especializados
│   ├── storage/cache_data/     # Cache persistente
│   ├── examples/               # Exemplos de schemas
│   └── pyproject.toml          # Dependências Poetry
├── frontend/
│   └── src/
│       ├── pages/Index.tsx     # Interface principal
│       └── components/         # Componentes React
├── docker-compose.yml          # Orquestração de containers
└── start.sh                    # Script de inicialização
```

## Monitoramento

### Endpoint de Estatísticas

```bash
curl http://localhost:8000/stats
```

O endpoint retorna métricas detalhadas sobre extrações totais, cache hits por nível, uso de heurísticas vs LLM, performance e consumo de tokens.

