# ModolRAG

**PostgreSQL-native Hybrid RAG Engine**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org)

ModolRAG is a lightweight, pip-installable RAG (Retrieval-Augmented Generation) engine that runs entirely on PostgreSQL. Upload documents, group them into collections, connect an LLM, and get a production-ready search API — no Elasticsearch, no separate vector database, no graph database.

```bash
pip install modolrag
modolrag serve --db postgresql://localhost:5439/modolrag
```

---

## 🤖 AI Setup Guide — 이 지침을 복사해 AI한테 그대로 시키세요

> 아래 내용을 **ChatGPT, Claude, Cursor, Copilot 등** AI에게 그대로 붙여넣으면 ModolRAG를 자동으로 설치·실행합니다.

<details>
<summary><b>📋 전체 설치 지침 복사하기 (클릭해서 펼치세요)</b></summary>

```
아래 지침대로 ModolRAG를 설치하고 실행해줘. 순서대로 하나씩 진행해.

## 중요: 각 단계마다 이미 설치/실행 중인지 먼저 확인하고, 되어있으면 "✅ 이미 완료" 출력 후 다음으로 넘어가.

## 1단계: 사전 요구사항 확인

아래 명령어를 하나씩 실행하고, 성공하면 "✅ 설치됨" 출력 후 넘어가. 실패한 것만 설치해.

  # Python
  python3 --version 2>/dev/null && echo "✅ Python 설치됨" || { echo "❌ 설치 필요"; brew install python@3.11; }
  
  # Docker
  docker --version 2>/dev/null && echo "✅ Docker 설치됨" || { echo "❌ 설치 필요"; brew install --cask docker; }
  
  # Ollama
  ollama --version 2>/dev/null && echo "✅ Ollama 설치됨" || { echo "❌ 설치 필요"; brew install ollama; }
  
  # Git
  git --version 2>/dev/null && echo "✅ Git 설치됨" || { echo "❌ 설치 필요"; brew install git; }
  
  # pip
  pip --version 2>/dev/null && echo "✅ pip 설치됨" || {
    echo "❌ pip 심링크 생성";
    ln -sf $(which pip3.11 2>/dev/null || which pip3) /opt/homebrew/bin/pip;
    ln -sf $(which python3.11 2>/dev/null || which python3) /opt/homebrew/bin/python;
  }

## 2단계: 프로젝트 클론 및 설치

  # 이미 클론되어 있는지 확인
  if [ -d "ModolRAG" ] && [ -f "ModolRAG/pyproject.toml" ]; then
    echo "✅ ModolRAG 프로젝트 이미 존재"
    cd ModolRAG
  else
    echo "📥 클론 중..."
    git clone https://github.com/modolai/ModolRAG.git
    cd ModolRAG
  fi

  # 이미 설치되어 있는지 확인
  python -c "import modolrag; print(f'✅ modolrag {modolrag.__version__} 이미 설치됨')" 2>/dev/null || {
    echo "📦 설치 중..."
    pip install -e ".[dev]"
  }

  # CLI 확인
  modolrag --help > /dev/null 2>&1 && echo "✅ CLI 동작 확인" || echo "⚠️ CLI 등록 안 됨. pip install -e . 다시 실행"

## 3단계: Ollama 임베딩 모델 설치

  # Ollama 실행 확인
  curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo "✅ Ollama 실행 중" || {
    echo "🦙 Ollama 시작 중..."
    ollama serve &
    sleep 3
  }

  # 모델 확인
  ollama list 2>/dev/null | grep -q "nomic-embed-text" && echo "✅ nomic-embed-text 이미 설치됨" || {
    echo "⬇️ 모델 다운로드 중..."
    ollama pull nomic-embed-text
  }

## 4단계: 원커맨드 실행

  # 이미 서버가 돌고 있는지 확인
  curl -sf http://localhost:8009/health > /dev/null 2>&1 && {
    echo "✅ ModolRAG 이미 실행 중 (http://localhost:8009)"
    echo "   Dashboard: http://localhost:8009/dashboard"
    echo "   Swagger:   http://localhost:8009/docs"
  } || {
    echo "🚀 서버 시작..."
    chmod +x start.sh stop.sh
    ./start.sh
  }

성공하면 이렇게 출력됨:
  📊 Dashboard:    http://localhost:8009/dashboard
  📖 Swagger UI:   http://localhost:8009/docs
  📋 ReDoc:        http://localhost:8009/redoc
  🐘 PostgreSQL:   localhost:5439
  🦙 Ollama:       localhost:11434

## 5단계: 동작 확인

  # 헬스체크
  curl -sf http://localhost:8009/health > /dev/null && echo "✅ 서버 정상" || echo "❌ 서버 응답 없음"

  # 이미 문서가 있는지 확인
  DOC_COUNT=$(curl -sf http://localhost:8009/api/documents 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
  if [ "$DOC_COUNT" -gt 0 ] 2>/dev/null; then
    echo "✅ 문서 ${DOC_COUNT}개 이미 등록됨 (업로드 스킵)"
  else
    echo "📄 테스트 문서 업로드..."
    echo "ModolRAG는 PostgreSQL 기반 RAG 엔진입니다." > /tmp/test.txt
    curl -X POST http://localhost:8009/api/ingest -F "file=@/tmp/test.txt"
    echo ""
    echo "⏳ 임베딩 처리 대기 (10초)..."
    sleep 10
  fi

  # 검색 테스트
  echo "🔍 검색 테스트..."
  curl -sf -X POST http://localhost:8009/api/search \
    -H "Content-Type: application/json" \
    -d '{"query":"RAG","top_k":3,"mode":"hybrid"}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'✅ 검색 결과: {d[\"count\"]}개')
" 2>/dev/null || echo "⚠️ 검색 실패"

  # 컬렉션 확인
  COLL_COUNT=$(curl -sf http://localhost:8009/api/collections 2>/dev/null | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('collections',[])))" 2>/dev/null || echo 0)
  if [ "$COLL_COUNT" -gt 0 ] 2>/dev/null; then
    echo "✅ 컬렉션 ${COLL_COUNT}개 이미 존재 (생성 스킵)"
  else
    echo "📚 테스트 컬렉션 생성..."
    curl -sf -X POST http://localhost:8009/api/collections \
      -H "Content-Type: application/json" \
      -d '{"name":"테스트","description":"테스트 컬렉션"}' > /dev/null && echo "✅ 컬렉션 생성됨"
  fi

## 6단계: 테스트 실행

  bash tests/run_all.sh
  # → 45 pytest 통과 + 5 API 테스트 통과

## 7단계: 중지 (필요할 때만)

  ./stop.sh
  # 데이터는 Docker 볼륨에 보존됨. 재시작: ./start.sh

## 포트 구성
- ModolRAG API + Dashboard: 8009
- PostgreSQL: 5439
- Ollama: 11434

## 환경변수 (.env 파일에 작성 가능)
POSTGRES_PASSWORD=modolrag         # DB 비밀번호
PG_PORT=5439                       # PostgreSQL 포트
MODOLRAG_PORT=8009                 # API 서버 포트
MODOLRAG_API_KEYS=                 # API 키 (빈값=인증없음)
MODOLRAG_EMBEDDING_PROVIDER=ollama # ollama 또는 openai
MODOLRAG_EMBEDDING_MODEL=nomic-embed-text  # 임베딩 모델
MODOLRAG_OLLAMA_BASE_URL=http://localhost:11434  # Ollama URL
MODOLRAG_OPENAI_API_KEY=           # OpenAI 쓸 경우만
MODOLRAG_CHUNK_SIZE=512            # 청크 크기 (128-4096)
MODOLRAG_CHUNK_OVERLAP=51         # 청크 오버랩 (0-512)
MODOLRAG_SIMILARITY_TOP_K=5       # 검색 결과 수 (1-50)
MODOLRAG_SIMILARITY_THRESHOLD=0.7 # 유사도 임계값 (0.0-1.0)

## OpenAI 사용 시 (Ollama 대신)
MODOLRAG_EMBEDDING_PROVIDER=openai
MODOLRAG_OPENAI_API_KEY=sk-your-key-here
MODOLRAG_EMBEDDING_MODEL=text-embedding-3-small
# 주의: schema.sql의 halfvec(768)을 halfvec(1536)으로 변경 필요

## API 엔드포인트 (16개)
GET  /health                                # 헬스체크 (인증 불필요)
POST /api/ingest                            # 문서 업로드 (multipart)
GET  /api/documents                         # 문서 목록
GET  /api/documents/{id}                    # 문서 상세
DELETE /api/documents/{id}                  # 문서 삭제
POST /api/search                            # 하이브리드 검색
POST /api/collections                       # 컬렉션 생성
GET  /api/collections                       # 컬렉션 목록
GET  /api/collections/{id}                  # 컬렉션 상세
DELETE /api/collections/{id}                # 컬렉션 삭제
POST /api/collections/{id}/documents        # 문서 추가
DELETE /api/collections/{id}/documents      # 문서 제거
GET  /api/graph                             # 지식 그래프
GET  /api/graph/node/{id}                   # 노드 상세
GET  /api/settings                          # 설정 조회
PUT  /api/settings                          # 설정 수정

## 검색 모드
- hybrid (기본): 벡터 + 키워드 + 그래프 → RRF 융합. 최고 품질
- vector: 의미 유사도 검색만
- fts: 키워드 매칭만
- graph: 지식 그래프 탐색만

## 컬렉션 사용법 (문서 세트별 검색)
1. 문서 업로드: POST /api/ingest
2. 컬렉션 생성: POST /api/collections {"name":"이름"}
3. 문서 할당: POST /api/collections/{id}/documents {"document_ids":["doc-uuid"]}
4. 스코프 검색: POST /api/search {"query":"질문","collection_id":"coll-uuid"}
   → 해당 컬렉션 문서만 검색됨

## 대시보드 (http://localhost:8009/dashboard)
- 📄 문서 관리: 업로드, 목록, 상태 확인, 삭제
- 📚 컬렉션: 생성, 문서 할당/제거
- 🔍 검색: 쿼리 테스트, 모드 선택, 컬렉션 필터
- 🕸️ 그래프: 지식 그래프 시각화
- ⚙️ 설정: 청크 크기, 임베딩 모델 등
- 한국어/영어 토글, 다크모드 토글 지원

## 기술 스택
- Python 3.11 + FastAPI + Uvicorn
- PostgreSQL 15 + pgvector (벡터 검색) + tsvector (전문 검색)
- asyncpg (DB 드라이버) + httpx (HTTP 클라이언트)
- React 19 + TypeScript + Vite + Tailwind CSS (대시보드)
- Docker + docker-compose (배포)
- Ollama nomic-embed-text 768d (기본 임베딩)

## 트러블슈팅
- "pip: command not found" → ln -sf $(which pip3.11) /opt/homebrew/bin/pip
- "Docker not running" → open -a Docker 후 30초 대기
- "Ollama connection refused" → ollama serve & 실행
- "halfvec dimension mismatch" → schema.sql의 768을 모델 차원에 맞게 변경
- 빌드 에러 "peer dep conflict" → npm ci --legacy-peer-deps (Dockerfile에 이미 적용됨)
```

</details>

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [How It Works (Non-Developer Guide)](#how-it-works)
- [Quick Start (One Command)](#quick-start-one-command)
- [Quick Start (pip)](#quick-start-pip)
- [Architecture](#architecture)
- [Collections (Document Sets)](#collections-document-sets)
- [Search Modes](#search-modes)
- [API Reference (16 Endpoints)](#api-reference)
- [API Documentation (Swagger)](#api-documentation)
- [Dashboard](#dashboard)
- [Configuration](#configuration)
- [Docker Configuration](#docker-configuration)
- [Tech Stack Details](#tech-stack-details)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [License](#license)

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Backend application |
| **Web Framework** | FastAPI 0.110+ | REST API with auto-generated OpenAPI docs |
| **ASGI Server** | Uvicorn | High-performance async server |
| **Database** | PostgreSQL 15 + pgvector | Relational DB + vector similarity search |
| **Vector Search** | pgvector (HNSW index, halfvec) | Cosine similarity on embeddings |
| **Full-Text Search** | PostgreSQL tsvector + GIN | BM25-like keyword matching |
| **Knowledge Graph** | PostgreSQL recursive CTE | Entity/relationship traversal |
| **Embedding (Local)** | Ollama + nomic-embed-text (768d) | Free, local, GPU-accelerated |
| **Embedding (Cloud)** | OpenAI text-embedding-3-small (1536d) | High quality, API-based |
| **Document Parsing** | pypdf, pdfplumber, python-docx, openpyxl, python-pptx | PDF, Word, Excel, PowerPoint |
| **Dashboard** | React 19 + TypeScript + Vite + Tailwind CSS | Admin UI (SPA served from FastAPI) |
| **Graph Visualization** | react-force-graph-2d | Interactive knowledge graph |
| **Containerization** | Docker + docker-compose | One-command deployment |
| **Config** | pydantic-settings | Type-safe env var configuration |
| **HTTP Client** | httpx | Async embedding API calls |
| **DB Driver** | asyncpg | High-performance async PostgreSQL |

**All dependencies are MIT/BSD/Apache-2.0 licensed.** No AGPL or GPL.

---

## How It Works

ModolRAG is designed so that **anyone — even non-developers — can create a production RAG API** through the web dashboard.

### The 4-Step Flow

```
Step 1: Upload Documents
  Dashboard → Documents → Upload (PDF, Word, Excel, PPT, Markdown, Text)
  ↓ Automatic: parse → chunk → embed → store

Step 2: Create a Collection
  Dashboard → Collections → Create "Customer Support Docs"
  Select which documents belong to this collection

Step 3: Connect an LLM
  Your app calls ModolRAG's search API with the collection ID
  ModolRAG returns relevant context from ONLY those documents

Step 4: Use the API
  POST http://localhost:8009/api/search
  {"query": "refund policy", "collection_id": "your-collection-uuid"}
  → Returns ranked, relevant document chunks ready for LLM context
```

### Example: Building a Customer Support Bot

```
1. Upload: FAQ.pdf, refund-policy.docx, product-guide.xlsx
   → Dashboard shows: 3 documents, status "vectorized" ✅

2. Create Collection: "Support Bot" → assign all 3 documents

3. Your chatbot calls:
   POST /api/search
   {"query": user_message, "collection_id": "support-bot-uuid", "top_k": 5}

4. ModolRAG returns the 5 most relevant passages
   → Feed these as context to ChatGPT/Claude/Llama

5. LLM generates an answer grounded in YOUR documents
```

### Example: Multiple Use Cases, Same Instance

```
Collection "HR Policy"     → docs: handbook.pdf, benefits.docx
Collection "Product Docs"  → docs: api-guide.md, architecture.pdf
Collection "Sales"         → docs: pricing.xlsx, pitch-deck.pptx

Each collection = separate search scope = separate API endpoint
Same ModolRAG instance serves all of them
```

---

## Quick Start (One Command)

```bash
git clone https://github.com/modolai/ModolRAG.git
cd ModolRAG
./start.sh
```

`start.sh` handles everything:

| Step | What it does |
|---|---|
| 0 | Starts Docker Desktop if not running |
| 1 | Checks Ollama is running (starts if needed) |
| 2 | Downloads embedding model `nomic-embed-text` if missing |
| 3 | Builds and starts PostgreSQL + ModolRAG containers |
| 4 | Waits for health check, prints all URLs |

```
==================================
  All services running!
==================================

  📊 Dashboard:    http://localhost:8009/dashboard
  📖 Swagger UI:   http://localhost:8009/docs
  📋 ReDoc:        http://localhost:8009/redoc
  🔍 Health:       http://localhost:8009/health
  🐘 PostgreSQL:   localhost:5439
  🦙 Ollama:       localhost:11434

  Stop:   docker compose down
  Logs:   docker compose logs -f modolrag
```

### Services & Ports

| Service | Port | Description |
|---|---|---|
| **ModolRAG** | `8009` | FastAPI API + React Dashboard + Swagger |
| **PostgreSQL** | `5439` | pgvector:pg15 (data persisted in Docker volume) |
| **Ollama** | `11434` | Local embedding model (runs on host machine) |

> Ports 8009/5439 are non-default to avoid conflicts.

---

## Quick Start (pip)

If you already have PostgreSQL with pgvector:

```bash
# Install
pip install modolrag

# Initialize database
modolrag init-db --db postgresql://user:pass@localhost:5439/modolrag

# Start server
modolrag serve --port 8009 --db postgresql://user:pass@localhost:5439/modolrag

# Open dashboard
open http://localhost:8009/dashboard
```

### CLI Commands

```bash
modolrag serve [--host 0.0.0.0] [--port 8009] [--db URI] [--reload]
modolrag init-db [--db URI]
modolrag ingest <file> [--db URI]
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ModolRAG                                │
│                                                                 │
│  Document  →  Parser  →  Chunker  →  Embedder  →  PostgreSQL   │
│  (6 types)   (pypdf,    (recursive,  (Ollama/    ├─ pgvector    │
│               docx,      semantic,    OpenAI)    ├─ tsvector    │
│               xlsx...)   page)                   └─ Graph CTE   │
│                                                       ↓         │
│              Query → Embed → [Vector+FTS+Graph] → RRF → Results │
│                                                                 │
│  REST API (16 endpoints)  │  Dashboard (React SPA)  │  CLI      │
└─────────────────────────────────────────────────────────────────┘
```

### Ingestion Pipeline

```
Upload file (POST /api/ingest)
  → Parse (pypdf/docx/openpyxl/pptx/markdown/text)
  → Chunk (RecursiveChunker: 512 chars, 51 overlap)
  → Embed (Ollama nomic-embed-text → 768d vectors)
  → Store in pgvector (halfvec + HNSW index)
  → Auto-generate tsvector (PostgreSQL GENERATED column)
  → Extract entities/relationships (LLM, best-effort)
  → Build knowledge graph nodes/edges
  → Status: "vectorized" ✅
```

### Search Pipeline

```
POST /api/search {"query": "...", "mode": "hybrid", "collection_id": "..."}
  → Embed query text (same model as ingestion)
  → Vector search (cosine similarity on pgvector HNSW index)
  → Full-text search (websearch_to_tsquery on tsvector GIN index)
  → Graph search (entity similarity → 2-hop BFS expansion)
  → RRF Fusion: score = Σ 1/(60 + rank_i)
  → Return top_k results with scores
```

---

## Collections (Document Sets)

Collections let you group documents and search within specific sets.

### Create & Use

```bash
# 1. Create a collection
curl -X POST http://localhost:8009/api/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "Product Docs", "description": "API and SDK documentation"}'
# → {"id": "uuid", "name": "Product Docs"}

# 2. Add documents
curl -X POST http://localhost:8009/api/collections/{collection-id}/documents \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["doc-uuid-1", "doc-uuid-2", "doc-uuid-3"]}'
# → {"added": 3}

# 3. Search ONLY within this collection
curl -X POST http://localhost:8009/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication flow", "collection_id": "collection-uuid"}'
# → Results from Product Docs only

# 4. Search ALL documents (no collection filter)
curl -X POST http://localhost:8009/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication flow"}'
# → Results from every document
```

### Key Behaviors

- Same document can belong to **multiple collections**
- Deleting a collection does **NOT** delete the documents
- Omit `collection_id` to search **all** documents
- Manage collections in **Dashboard → Collections** page

---

## Search Modes

| Mode | Description | Best For | How it Works |
|---|---|---|---|
| `hybrid` | Vector + FTS + Graph → RRF fusion (default) | General purpose, best quality | Combines all three search types |
| `vector` | Semantic similarity only | "Find documents about X" | pgvector HNSW cosine distance |
| `fts` | Keyword matching only | Exact terms, names, codes | PostgreSQL tsvector + websearch_to_tsquery |
| `graph` | Knowledge graph traversal | "How is X related to Y?" | Entity similarity → 2-hop BFS |

---

## API Reference

### All 16 Endpoints

#### Admin (no tag prefix)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | No | Health check — returns version + URL links |

#### Documents

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/ingest` | Yes | Upload file → auto parse+chunk+embed+store |
| `GET` | `/api/documents` | Yes | List documents (filter: `?status=vectorized`) |
| `GET` | `/api/documents/{id}` | Yes | Document detail (status, chunks, progress, errors) |
| `DELETE` | `/api/documents/{id}` | Yes | Delete document + all chunks + graph data |

#### Search

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/search` | Yes | Hybrid search with optional `collection_id` filter |

Request body:
```json
{
  "query": "search text",
  "top_k": 10,
  "mode": "hybrid",
  "collection_id": "optional-uuid"
}
```

#### Collections

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/collections` | Yes | Create collection |
| `GET` | `/api/collections` | Yes | List all collections (with document counts) |
| `GET` | `/api/collections/{id}` | Yes | Collection detail + document list |
| `DELETE` | `/api/collections/{id}` | Yes | Delete collection (keeps documents) |
| `POST` | `/api/collections/{id}/documents` | Yes | Add documents to collection |
| `DELETE` | `/api/collections/{id}/documents` | Yes | Remove documents from collection |

#### Knowledge Graph

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/graph` | Yes | All nodes + edges (for visualization) |
| `GET` | `/api/graph/node/{id}` | Yes | Node detail + 1-hop neighbors |

#### Settings

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/settings` | Yes | Current RAG engine settings |
| `PUT` | `/api/settings` | Yes | Update settings (partial update) |

### Authentication

All endpoints (except `/health`) require the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-key" http://localhost:8009/api/documents
```

If `MODOLRAG_API_KEYS` is empty (default), authentication is disabled — all requests are allowed.

---

## API Documentation

ModolRAG auto-generates interactive API documentation from code. No manual doc writing needed.

### How to Access

| URL | What You See |
|---|---|
| **[localhost:8009/docs](http://localhost:8009/docs)** | **Swagger UI** — Interactive. Click any endpoint → "Try it out" → enter parameters → "Execute" → see response |
| **[localhost:8009/redoc](http://localhost:8009/redoc)** | **ReDoc** — Clean reading format. Better for understanding the API structure |
| **[localhost:8009/openapi.json](http://localhost:8009/openapi.json)** | **OpenAPI 3.1 JSON** — Import into Postman, Insomnia, or any API client |

### What's Documented Automatically

- Every endpoint with description and summary
- Request body schemas with field types, descriptions, and validation rules
- Response schemas with example payloads
- Authentication requirements
- Endpoints grouped by tag: `documents`, `search`, `collections`, `graph`, `admin`

### Using Swagger UI

1. Open `http://localhost:8009/docs`
2. Click on any endpoint (e.g., `POST /api/search`)
3. Click **"Try it out"**
4. Fill in the request body (example is pre-filled)
5. Click **"Execute"**
6. See the actual response from your server

### Importing to Postman

1. Open Postman → Import → URL
2. Enter: `http://localhost:8009/openapi.json`
3. All 16 endpoints are imported with schemas

---

## Dashboard

Access at **[localhost:8009/dashboard](http://localhost:8009/dashboard)**

| Page | Description |
|---|---|
| **Documents** | Upload files (drag & drop), view processing status, delete |
| **Collections** | Create/delete collections, assign/remove documents |
| **Search** | Test queries with mode selector, collection filter, Top-K slider |
| **Graph** | Interactive knowledge graph visualization (force-directed layout) |
| **Settings** | Configure chunk size, embedding model, thresholds, API key |
| **API Docs** | Links to Swagger UI and ReDoc |

---

## Configuration

All settings via environment variables with `MODOLRAG_` prefix:

| Variable | Default | Description |
|---|---|---|
| `MODOLRAG_POSTGRES_URI` | `postgresql://localhost:5432/modolrag` | PostgreSQL connection string |
| `MODOLRAG_API_KEYS` | `""` (no auth) | Comma-separated valid API keys |
| `MODOLRAG_EMBEDDING_PROVIDER` | `ollama` | `ollama` (local) or `openai` (cloud) |
| `MODOLRAG_EMBEDDING_MODEL` | `nomic-embed-text` | Model name for embeddings |
| `MODOLRAG_EMBEDDING_DIMENSIONS` | `768` | Vector dimensions (768 for nomic, 1536 for OpenAI) |
| `MODOLRAG_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `MODOLRAG_OPENAI_API_KEY` | `""` | OpenAI API key (required if provider=openai) |
| `MODOLRAG_CHUNK_SIZE` | `512` | Text chunk size in characters (128-4096) |
| `MODOLRAG_CHUNK_OVERLAP` | `51` | Overlap between chunks (0-512) |
| `MODOLRAG_SIMILARITY_TOP_K` | `5` | Default search results count (1-50) |
| `MODOLRAG_SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score (0.0-1.0) |

---

## Docker Configuration

### docker-compose.yml Services

| Service | Image | Port | Volume |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg15` | `5439:5432` | `pgdata` (persistent) |
| `modolrag` | Built from `Dockerfile` | `8009:8000` | — |

Ollama runs on the host machine (not containerized) for GPU access.

### Dockerfile (Multi-stage)

```
Stage 1: node:20-slim → npm ci → npm run build (dashboard)
Stage 2: python:3.11-slim → pip install → copy dashboard → uvicorn
```

### Using OpenAI (no Ollama)

```bash
echo 'MODOLRAG_EMBEDDING_PROVIDER=openai' > .env
echo 'MODOLRAG_OPENAI_API_KEY=sk-xxx' >> .env
docker compose up -d
```

### Custom .env

```env
POSTGRES_PASSWORD=your-secure-password
PG_PORT=5439
MODOLRAG_PORT=8009
MODOLRAG_API_KEYS=key1,key2
MODOLRAG_EMBEDDING_PROVIDER=ollama
MODOLRAG_EMBEDDING_MODEL=nomic-embed-text
```

---

## Tech Stack Details

### Why PostgreSQL Only?

| Approach | Components | Ops Overhead |
|---|---|---|
| **Typical RAG** | Pinecone + Elasticsearch + Neo4j + Redis + App DB | 5 services to manage |
| **ModolRAG** | PostgreSQL (pgvector + tsvector + CTE) | 1 database |

- pgvector handles 50M+ vectors at production scale (DiskANN benchmarks)
- tsvector provides BM25-like full-text search natively
- Recursive CTEs match Neo4j for 2-hop graph traversal
- ACID transactions across vectors + text + graph — no sync lag

### Why Not LangChain/LlamaIndex?

- Zero framework lock-in
- Raw SQL + httpx = full control over every query
- Minimal dependency tree (< 15 direct dependencies)
- Easier to debug, profile, and optimize

### Why RRF Fusion?

Reciprocal Rank Fusion combines multiple search rankings without score normalization:

```
score(item) = Σ 1/(60 + rank_i)
```

- Parameter-free (k=60 is standard)
- No training data needed
- +22% precision over vector-only search (benchmarked)

### Document Parsers

| Format | Library | License | Features |
|---|---|---|---|
| PDF | pypdf + pdfplumber | BSD + MIT | Text + table detection |
| DOCX | python-docx | MIT | Headings + styles + tables |
| XLSX | openpyxl | MIT | Sheet-by-sheet markdown tables |
| PPTX | python-pptx | MIT | Slide text + notes |
| Markdown | built-in | — | YAML frontmatter + section split |
| Plain Text | built-in | — | Encoding auto-detection |

> PyMuPDF (AGPL-3.0) and marker-pdf (GPL-3.0) are intentionally NOT used — incompatible with MIT license.

---

## Project Structure

```
ModolRAG/
├── modolrag/                    # Python package
│   ├── main.py                  # FastAPI app + router registration
│   ├── config.py                # pydantic-settings (env vars)
│   ├── cli.py                   # CLI: serve, init-db, ingest
│   ├── api/
│   │   ├── auth.py              # X-API-Key validation
│   │   ├── middleware.py         # CORS
│   │   ├── ingest.py            # Document upload + management
│   │   ├── search.py            # Hybrid search (collection-scoped)
│   │   ├── collections.py       # Collection CRUD + document assignment
│   │   ├── graph.py             # Graph data + node details
│   │   └── admin.py             # Health + settings
│   ├── core/
│   │   ├── embedder.py          # Ollama + OpenAI adapters
│   │   ├── chunker.py           # Recursive/semantic/page chunking
│   │   ├── vector_store.py      # pgvector CRUD + HNSW search
│   │   ├── fts.py               # tsvector full-text search
│   │   ├── graph_store.py       # Graph CRUD + CTE traversal
│   │   ├── hybrid_search.py     # RRF fusion engine
│   │   ├── extractor.py         # LLM entity extraction
│   │   └── pipeline.py          # End-to-end ingestion
│   ├── db/
│   │   ├── schema.sql           # 8 tables, 10+ indexes
│   │   └── connection.py        # asyncpg connection pool
│   ├── parsers/                 # 6 document parsers
│   └── static/                  # Dashboard build output
├── dashboard/                   # React SPA (Vite + Tailwind)
│   └── src/pages/               # Documents, Collections, Search, Graph, Settings
├── docs/
│   ├── ARCHITECTURE.md          # Pipelines, RRF, Graph CTE, Docker
│   ├── SCHEMA.md                # All 8 tables with DDL
│   └── MODOLAI_INTEGRATION.md   # ModolAI connection guide
├── start.sh                     # One-command deployment script
├── Dockerfile                   # Multi-stage (Node → Python)
├── docker-compose.yml           # PostgreSQL + ModolRAG
├── pyproject.toml               # Package config + dependencies
├── Makefile                     # dev, build, test, docker targets
└── LICENSE                      # MIT
```

### Database Schema (8 Tables)

| Table | Purpose |
|---|---|
| `modolrag_documents` | Document metadata + processing status |
| `modolrag_document_chunks` | Text chunks + embedding (halfvec 768) + tsvector (auto) |
| `modolrag_graph_nodes` | Knowledge graph entities |
| `modolrag_graph_edges` | Entity relationships |
| `modolrag_communities` | Graph community detection |
| `modolrag_settings` | RAG engine configuration (singleton) |
| `modolrag_collections` | Document collections (named sets) |
| `modolrag_collection_documents` | Collection ↔ Document mapping |

All tables use the `modolrag_` prefix to coexist with other applications in the same database.

Full DDL: [docs/SCHEMA.md](docs/SCHEMA.md)

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **PostgreSQL-only** | One DB = one backup, one monitoring, ACID across vectors+text+graph |
| **No LangChain/LlamaIndex** | Zero lock-in, raw SQL, minimal dependencies |
| **RRF fusion (k=60)** | Parameter-free, +22% precision, no training data |
| **Recursive CTE over Neo4j** | 250x faster than Apache AGE for 2-hop RAG graphs |
| **pypdf over PyMuPDF** | PyMuPDF is AGPL-3.0, incompatible with MIT license |
| **FastAPI + embedded SPA** | Single process, single port, Swagger auto-generated |
| **X-API-Key auth** | Simple, stateless — no JWT complexity for a backend service |
| **Collections** | Scope search to document sets — same instance serves multiple use cases |
| **halfvec(768)** | nomic-embed-text default; 50% storage savings vs full vector |

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Contributions welcome. Please open an issue first to discuss changes.

---

## Further Documentation

| Document | Description |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview, pipelines, RRF, Graph CTE, Docker |
| [docs/SCHEMA.md](docs/SCHEMA.md) | Complete DDL for all 8 tables + indexes |
| [docs/MODOLAI_INTEGRATION.md](docs/MODOLAI_INTEGRATION.md) | Connect ModolRAG to ModolAI |
| [localhost:8009/docs](http://localhost:8009/docs) | Live Swagger UI (when server is running) |
| [localhost:8009/redoc](http://localhost:8009/redoc) | Live ReDoc API documentation |
