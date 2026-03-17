# ModolRAG — 오픈소스 RAG 엔진 프로젝트 구축

## TL;DR

> **Quick Summary**: PostgreSQL(pgvector) 기반 하이브리드 RAG 엔진을 별도 오픈소스 레포로 구축. 벡터+전문검색+지식그래프를 RRF로 융합하는 검색 파이프라인, FastAPI 백엔드 + React SPA 대시보드, pip 설치 가능한 패키지로 제공.
>
> **Deliverables**:
> - ModolRAG Python 패키지 (pip install modolrag)
> - FastAPI REST API (ingest, search, graph, admin)
> - PostgreSQL 스키마 (pgvector + 그래프 테이블)
> - React SPA 대시보드 (문서관리, 검색, 그래프시각화, 설정)
> - Docker Compose 배포
> - ModolAI 연동 가이드
>
> **Estimated Effort**: XL
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: T1(스캐폴딩) → T3(DB스키마) → T5(벡터스토어) → T8(하이브리드검색) → T13(API통합) → T16(대시보드) → Final

---

## Context

### Original Request
사용자가 ModolAI(기존 AI 챗 플랫폼)에 RAG 기능을 추가하고자 함. 기존 프레임워크(LangChain, LlamaIndex)를 사용하지 않고 직접 오픈소스를 제작하여 ModolAI에 연동. Simple RAG(벡터+FTS)와 Graph RAG(Obsidian 스타일 지식 그래프) 둘 다 포함.

### Interview Summary
**Key Discussions**:
- 임베딩: Ollama 로컬(nomic-embed-text 768d) + OpenAI API(text-embedding-3-small 1536d) 둘 다 지원
- 문서: PDF, Markdown, Plain Text, Word/Excel/PPT
- Graph RAG: v1부터 벡터+FTS+그래프 전부 포함
- 프레임워크: FastAPI + 내장 React SPA (Vite). 프로세스 1개, pip 배포 가능
- DB: 같은 PostgreSQL + `modolrag_` 프리픽스 테이블. Supabase 호환
- 인증: X-API-Key 헤더 방식
- 그래프 시각화: v1에 react-force-graph 포함
- 대상: 개발자(pip) + 엔드유저(대시보드)

**Research Findings**:
- pgvector: HNSW 인덱스, halfvec 최대 4000dim, Supabase 네이티브 지원
- 하이브리드 검색(벡터+FTS+RRF): 순수 벡터 대비 +22% 정밀도
- Graph RAG: k-core > Leiden (PostgreSQL에서 결정론적, O(|E|))
- 500+⭐ RAG 프로젝트 전수: 100% Python/FastAPI 사용, Next.js 단독 0건
- 증분 업데이트: ON CONFLICT DO UPDATE로 원자적 업서트

### Metis Review
**Identified Gaps** (addressed):
- DB 분리 전략 → 같은 DB + `modolrag_` 프리픽스로 결정
- API 인증 → X-API-Key 방식으로 결정
- ModolAI 기존 rag_* 테이블과의 충돌 → modolrag_ 프리픽스로 공존
- 대용량 파일 처리 타임아웃 → 비동기 처리 + 상태 폴링

---

## Work Objectives

### Core Objective
`/Users/kimjiwon/Desktop/kimjiwon/ModolRAG/` 에 완전한 RAG 엔진 프로젝트를 구축. pip 설치 가능하고, Docker Compose로 즉시 실행 가능하며, ModolAI와 HTTP API로 연동 가능한 상태까지.

### Concrete Deliverables
- `modolrag/` Python 패키지 — 코어 엔진 + FastAPI 서버
- `dashboard/` React SPA — 대시보드 프론트엔드
- `docker-compose.yml` — PostgreSQL + ModolRAG 원클릭 실행
- `pyproject.toml` — pip install 가능한 패키지 설정
- `README.md` — 프로젝트 문서
- `docs/ARCHITECTURE.md` — 아키텍처 상세
- `docs/SCHEMA.md` — DB 스키마 설계

### Definition of Done
- [ ] `pip install -e .` 성공
- [ ] `modolrag serve --db $POSTGRES_URI` 로 서버 기동
- [ ] `curl POST /api/ingest` 로 PDF 업로드 → 청킹 → 임베딩 → DB 저장
- [ ] `curl POST /api/search` 로 하이브리드 검색 결과 반환
- [ ] `curl GET /api/graph` 로 그래프 데이터 반환
- [ ] `http://localhost:8000/dashboard` 에서 대시보드 접속
- [ ] `docker compose up -d` 로 전체 스택 실행

### Must Have
- pgvector HNSW 인덱스 벡터 검색
- tsvector + GIN 전문 검색
- Recursive CTE 그래프 탐색 (2홉)
- RRF 융합 검색 (벡터+FTS+그래프)
- 문서 파서 6종 (PDF, DOCX, XLSX, PPTX, MD, TXT)
- Ollama + OpenAI 임베딩 어댑터
- LLM 엔티티/관계 추출
- React 대시보드 (Documents, Search, Graph, Settings)
- X-API-Key 인증
- Supabase 호환 (표준 POSTGRES_URI)
- `modolrag_` 테이블 프리픽스

### Must NOT Have (Guardrails)
- LangChain, LlamaIndex, Pinecone 등 외부 RAG 프레임워크 의존성
- Neo4j, Weaviate 등 외부 벡터/그래프 DB
- Next.js, SSR, 서버 컴포넌트 (대시보드는 React SPA)
- Streamlit, Gradio (대시보드)
- ModolAI 코드 직접 수정 (연동은 가이드 문서로 제공)
- Supabase Edge Functions 의존 (표준 PostgreSQL만 사용)
- 3홉 이상 그래프 탐색 (노이즈 > 시그널)
- **AGPL/GPL 라이선스 의존성** — pymupdf(AGPL), pymupdf4llm(AGPL), marker-pdf(GPL) 사용 금지. MIT 프로젝트와 호환 불가

---

## License Compliance

> ModolRAG는 **MIT 라이선스**로 배포. 모든 의존성은 MIT/BSD/Apache-2.0 이하 허용적 라이선스만 허용.

### 왜 기존 라이브러리를 가져다 써도 되는가

**pip 의존성으로 사용하는 것은 업계 표준이며 완전히 합법입니다.**

- **pip 의존성 = 별개 저작물**: `pyproject.toml`에 의존성으로 명시하고 사용자가 `pip install`로 설치하는 방식은 남의 코드를 "포함"하는 것이 아니라 "참조"하는 것. 법적으로 별개의 저작물로 취급
- **허용적 라이선스(MIT/BSD/Apache)**: 상업적 사용, 수정, 재배포 전부 자유. 저작권 고지만 유지하면 됨
- **업계 관행**: FastAPI, Django, Flask 등 모든 Python 프레임워크가 동일 방식. PyPI에 등록된 50만+ 패키지가 이 구조
- **주의점**: AGPL/GPL 라이브러리는 pip 의존성이라도 "결합 저작물"로 해석될 수 있어 카피레프트 전파 위험 → 금지 목록으로 관리

### ✅ 허용 의존성

| 라이브러리 | 라이선스 | 용도 |
|---|---|---|
| `docling` | MIT (IBM → Linux Foundation) | PDF/DOCX/PPTX/XLSX 파싱 (메인 파서) |
| `pypdf` | BSD-3-Clause | PDF 텍스트 추출 (경량 폴백) |
| `python-docx` | MIT | DOCX 파싱 |
| `openpyxl` | MIT | XLSX 파싱 |
| `python-pptx` | MIT | PPTX 파싱 |
| `fastapi` | MIT | 웹 프레임워크 |
| `uvicorn` | BSD-3-Clause | ASGI 서버 |
| `asyncpg` | Apache-2.0 | PostgreSQL 드라이버 |
| `httpx` | BSD-3-Clause | HTTP 클라이언트 |
| `pydantic-settings` | MIT | 설정 관리 |
| `unstructured` | Apache-2.0 | (선택) 범용 문서 파서 |
| `markitdown` | MIT (Microsoft) | (선택) PDF→Markdown 변환 |

### 🚫 금지 의존성

| 라이브러리 | 라이선스 | 금지 사유 |
|---|---|---|
| `pymupdf` (PyMuPDF) | **AGPL-3.0** | 네트워크 서비스 제공 시 전체 소스 AGPL 공개 의무. MIT와 호환 불가 |
| `pymupdf4llm` | **AGPL-3.0** | pymupdf 래퍼, 동일 문제 |
| `marker-pdf` | **GPL-3.0** | 카피레프트. MIT 프로젝트 배포 시 GPL로 전환 필요. 모델 가중치도 상업용 제한 |

### 대안 전략
- **PDF 고품질 파싱**: `docling` — IBM이 개발, Linux Foundation 기부. 레이아웃 분석+테이블 추출+OCR 지원. RAGFlow의 DeepDoc에 준하는 품질
- **PDF 경량 폴백**: `pypdf` — 순수 Python, 의존성 최소
- **PDF→Markdown**: `markitdown` (Microsoft, MIT) — 다양한 포맷 지원

---

## Competitive Positioning

### 핵심 포지셔닝 메시지

> **"PostgreSQL 하나로 완성하는 하이브리드 RAG 엔진. pip install 한 줄이면 벡터 검색 + 전문 검색 + 지식 그래프가 즉시 동작합니다."**

### 시장에서 비어있는 자리

```
                기능 완전(서버+대시보드+API)
                       ↑
                       │
  RAGFlow ●            │
  (Docker 5+컨테이너)   │
  (ES+MySQL+MinIO)      │
                       │        ● ← ModolRAG 목표 포지션
  AnythingLLM ●        │          (pip install, PG-only, 풀스택)
  (Node.js, 벡터only)  │
                       │
  ─────────────────────┼──────────────────────→
  무거운 인프라          │          경량 / 개발자 친화
                       │
  R2R ● 💀             │
  (동일 아키텍처,       │
   9개월째 릴리즈 없음)  │
                       │
  LightRAG ●           │
  (그래프 특화,         │
   파서/서버 없음)       │
                  라이브러리/CLI만
```

**R2R이 증명하고 죽으면서 남긴 빈자리:**
- PostgreSQL + pgvector + FTS + RRF 아키텍처는 R2R(YC 투자)이 검증
- 2025년 6월 이후 9개월째 릴리즈 없음 → 사실상 개발 중단
- 동일 기술 스택을 더 나은 실행력으로 채울 기회

### 경쟁자별 차별점

| vs. | ModolRAG 우위 | 그들의 우위 |
|---|---|---|
| **RAGFlow** (75K⭐) | pip install, PG 단일DB, 인프라 1/5 | DeepDoc 파싱, 커뮤니티 규모, 에이전트 |
| **LightRAG** (29K⭐) | 풀스택(서버+대시보드+API), 하이브리드 3중 검색 | 그래프 특화 학술 품질, EMNLP 논문 |
| **AnythingLLM** (54K⭐) | Python 생태계, 하이브리드+그래프 검색 | 데스크톱 앱, 비개발자 UX |
| **GraphRAG** (31K⭐) | 서버/API/대시보드, 인덱싱 비용 99% 절감 | Global 질의, MS Research 학술 |
| **Kotaemon** (25K⭐) | React SPA (화이트라벨 가능), PG 네이티브 | Gradio 즉시 실행, PDF 인용 뷰어 |
| **R2R** (7.7K⭐) | 활발한 개발, React 대시보드, Graph 시각화 | (개발 중단 상태) |

### 안티-타겟 (경쟁하지 않을 영역)

- ❌ **문서 파싱 최강** — RAGFlow DeepDoc이 압도적. docling으로 "충분히 좋은" 수준 목표
- ❌ **비개발자 시장** — AnythingLLM의 데스크톱 앱 영역
- ❌ **학술 그래프 RAG** — LightRAG/GraphRAG의 연구 영역
- ✅ **개발자가 pip install로 즉시 쓸 수 있는 프로덕션 RAG 엔진** — 이것만 집중

---

## Graph RAG Differentiation

### ModolRAG의 Graph RAG ≠ LightRAG/GraphRAG

기존 Graph RAG 프로젝트들과의 근본적 차이:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Graph RAG 접근 방식 비교                       │
├─────────────────────┬─────────────────┬─────────────────────────┤
│ MS GraphRAG         │ LightRAG        │ ModolRAG                │
├─────────────────────┼─────────────────┼─────────────────────────┤
│ Leiden 커뮤니티 감지  │ 듀얼레벨 그래프  │ PostgreSQL 네이티브 CTE │
│ Parquet/Azure 저장   │ Neo4j/NetworkX  │ 같은 DB, 같은 트랜잭션  │
│ 전체 재인덱싱 필요    │ 증분 업데이트    │ ON CONFLICT DO UPDATE   │
│ 인덱싱 $33K+        │ 토큰 99% 절감   │ SQL 기반, LLM 비용 최소 │
│ CLI만, 서버 없음     │ 기본 UI         │ 풀스택 (API+대시보드)   │
│ 별도 그래프 DB 필요   │ 별도 그래프 DB   │ PostgreSQL에 통합       │
└─────────────────────┴─────────────────┴─────────────────────────┘
```

### ModolRAG Graph RAG의 핵심 가치: "같은 DB, 같은 트랜잭션"

**기존 문제**: 대부분의 Graph RAG는 벡터 DB + 그래프 DB + 메타데이터 DB를 각각 운영
- 데이터 동기화 문제 (문서 삭제 시 그래프 노드가 남음)
- 3개 DB의 운영/백업/모니터링 비용
- 트랜잭션 보장 불가 (eventual consistency)

**ModolRAG 해결**: 벡터 + FTS + 그래프가 **하나의 PostgreSQL에서 하나의 트랜잭션**으로 동작
```sql
BEGIN;
  -- 1. 벡터 검색으로 시드 청크 추출
  -- 2. 시드 청크의 엔티티로 2홉 그래프 확장
  -- 3. FTS로 키워드 매칭
  -- 4. RRF로 3개 결과 융합
  -- 전부 하나의 SQL, 하나의 트랜잭션
COMMIT;
```

### 벤치마크 근거: PostgreSQL CTE가 충분한 이유

| 벤치마크 | PostgreSQL BFS CTE | Apache AGE shortestPath | Neo4j |
|---|---|---|---|
| 10K 노드 최단경로 | **0.09ms** | 23ms | ~1ms |
| 100K 노드 최단경로 | **0.33ms** | 23ms | ~2ms |
| 2홉 이웃 탐색 | **< 1ms** | — | ~1ms |

RAG 지식 그래프는 일반적으로 2-3홉 탐색이 핵심. 이 범위에서 PostgreSQL CTE는 Neo4j와 동등하며, Apache AGE보다 250배 빠름.

### 포지셔닝 요약

> **"Graph RAG의 학술적 최전선이 아니라, 프로덕션에서 실제로 동작하는 실용적 Graph RAG. 별도 그래프 DB 없이, 같은 PostgreSQL에서, ACID 트랜잭션으로."**

---

## ModolAI Integration Bridge

### 기존 ModolAI RAG 인프라 현황

ModolAI에는 이미 3개의 RAG 관련 테이블이 존재:

| ModolAI 기존 테이블 | 용도 | ModolRAG 대응 |
|---|---|---|
| `rag_documents` | 문서 저장 (status, vectors JSONB) | `modolrag_documents` |
| `rag_models` | RAG 모델 설정 (선택 문서, 파라미터) | `modolrag_settings` |
| `rag_settings` | 전역 설정 (LanceDB 경로, 청크 크기) | `modolrag_settings` |

### 핵심 불일치와 해결

| 항목 | ModolAI 기존 | ModolRAG | 해결 |
|---|---|---|---|
| 벡터 저장소 | LanceDB (파일 기반) | pgvector (PostgreSQL) | ModolRAG가 대체. LanceDB 코드 제거 불필요 (공존) |
| 벡터 컬럼 | `vectors` JSONB | `embedding halfvec(1536)` | ModolRAG는 별도 테이블 (`modolrag_` 프리픽스) |
| 문서 상태 | 동일 (uploaded→processing→indexed) | 동일 | 호환 |
| 임베딩 모델 | nomic-embed-text (768d) | nomic-embed-text (768d) + OpenAI (1536d) | 호환, 확장 |
| API 인증 | JWT + API 토큰 | X-API-Key | ModolAI에서 X-API-Key 전달 |

### 연동 아키텍처

```
┌──────────────────────────────────────────────────┐
│ ModolAI (Next.js)                                │
│                                                  │
│  채팅 → completions API ─┐                       │
│                          ├→ ModolRAG 호출 여부 판단│
│  /v1/embeddings ─────────┘                       │
│                                                  │
│  환경변수:                                        │
│    MODOLRAG_URL=http://localhost:8000             │
│    MODOLRAG_API_KEY=xxx                          │
│                                                  │
└──────────────┬───────────────────────────────────┘
               │ HTTP (X-API-Key)
               ▼
┌──────────────────────────────────────────────────┐
│ ModolRAG (FastAPI)                               │
│                                                  │
│  POST /api/ingest  ← 문서 수집                    │
│  POST /api/search  ← 하이브리드 검색              │
│  GET  /api/graph   ← 그래프 데이터                │
│  GET  /dashboard   ← 관리 대시보드                │
│                                                  │
│  DB: 같은 PostgreSQL, modolrag_* 테이블          │
└──────────────────────────────────────────────────┘
```

### 마이그레이션 경로 (기존 ModolAI RAG 사용자)

**Phase 1: 공존** (ModolRAG v1)
- ModolAI의 기존 `rag_*` 테이블은 그대로 유지
- ModolRAG는 `modolrag_*` 프리픽스로 별도 테이블 사용
- 같은 PostgreSQL 인스턴스에서 공존
- ModolAI가 ModolRAG API를 HTTP로 호출

**Phase 2: 마이그레이션 도구** (ModolRAG v1.x)
- `modolrag migrate --from-modolai` CLI 명령
- `rag_documents` → `modolrag_documents` 데이터 이전
- LanceDB 벡터 → pgvector 재임베딩 (벡터 포맷 비호환으로 재임베딩 필수)
- 기존 `rag_settings` → `modolrag_settings` 설정 매핑

**Phase 3: 네이티브 통합** (ModolAI v-next)
- ModolAI 채팅에서 RAG 토글 시 ModolRAG API 자동 호출
- ModolAI 관리자 패널에서 ModolRAG 설정 프록시
- 문서 T22 (ModolAI 연동 가이드)에서 상세 안내

### 기존 API 재활용

ModolAI에 이미 존재하는 엔드포인트를 ModolRAG가 활용:
- **`/v1/embeddings`**: ModolRAG가 임베딩 생성 시 ModolAI의 기존 엔드포인트 호출 가능 (Ollama/OpenAI 라우팅 이미 구현됨)
- **`/v1/rerank`**: 검색 결과 재정렬에 활용 가능
- **API 토큰 시스템**: ModolAI의 기존 토큰을 ModolRAG의 X-API-Key로 브릿지

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (새 프로젝트)
- **Automated tests**: YES (Tests-after) — pytest
- **Framework**: pytest + httpx (FastAPI TestClient)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **API**: Bash (curl) — Send requests, assert status + response fields
- **Library/Module**: Bash (python -c) — Import, call functions, compare output
- **Dashboard**: Playwright — Navigate, interact, screenshot
- **Docker**: Bash — docker compose up, health check

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — 즉시 시작):
├── T1: 프로젝트 스캐폴딩 + pyproject.toml [quick]
├── T2: 프로젝트 문서 (README, ARCHITECTURE, SCHEMA) [writing]
├── T3: DB 스키마 + 커넥션 모듈 [quick]
├── T4: 설정 관리 + API Key 인증 미들웨어 [quick]
└── T5: 임베딩 어댑터 (Ollama + OpenAI) [quick]

Wave 2 (Core Modules — Wave 1 후):
├── T6: 문서 파서 6종 (PDF/DOCX/XLSX/PPTX/MD/TXT) [unspecified-high]
├── T7: 청킹 엔진 (recursive, semantic, page) [deep]
├── T8: 벡터 스토어 (pgvector CRUD + HNSW 검색) [deep]
├── T9: 전문 검색 (tsvector + GIN) [unspecified-high]
├── T10: 그래프 스토어 (노드/엣지 CRUD + CTE 탐색) [deep]
└── T11: LLM 엔티티/관계 추출기 [deep]

Wave 3 (Integration — Wave 2 후):
├── T12: 하이브리드 검색 + RRF 융합 [deep]
├── T13: FastAPI 라우터 통합 (ingest/search/graph/admin) [unspecified-high]
├── T14: 수집 파이프라인 (업로드→파싱→청킹→임베딩→그래프) [deep]
├── T15: CLI 엔트리포인트 (modolrag serve) [quick]
└── T16: Docker Compose + Makefile [quick]

Wave 4 (Dashboard + Polish — Wave 3 후):
├── T17: 대시보드 스캐폴딩 (Vite + React + Tailwind) [visual-engineering]
├── T18: Documents 페이지 (업로드/목록/상태) [visual-engineering]
├── T19: Search 페이지 (쿼리 테스트/결과 표시) [visual-engineering]
├── T20: Graph 페이지 (react-force-graph 시각화) [visual-engineering]
├── T21: Settings 페이지 + 대시보드 빌드 → static/ [visual-engineering]
└── T22: ModolAI 연동 가이드 문서 [writing]

Wave FINAL (검증):
├── F1: 플랜 준수 감사 (oracle)
├── F2: 코드 품질 리뷰 (unspecified-high)
├── F3: E2E QA — curl + Playwright (unspecified-high)
└── F4: 스코프 충실도 검증 (deep)

Critical Path: T1 → T3 → T8 → T12 → T13 → T14 → T17 → F1-F4
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 6 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| T1 | — | T2-T22 |
| T2 | T1 | — (문서, 비차단) |
| T3 | T1 | T6-T14 |
| T4 | T1 | T13 |
| T5 | T1 | T7, T8, T14 |
| T6 | T3 | T14 |
| T7 | T3, T5 | T14 |
| T8 | T3, T5 | T12 |
| T9 | T3 | T12 |
| T10 | T3, T5 | T11, T12 |
| T11 | T10, T5 | T14 |
| T12 | T8, T9, T10 | T13, T14 |
| T13 | T4, T12 | T14 |
| T14 | T6, T7, T11, T13 | T15, T16 |
| T15 | T14 | — |
| T16 | T14 | — |
| T17 | T1 | T18-T21 |
| T18-T21 | T17, T13 | — |
| T22 | T14 | — |
| F1-F4 | T1-T22 | — |

### Agent Dispatch Summary

- **Wave 1**: 5 tasks — T1-T4 → `quick`, T2 → `writing`, T5 → `quick`
- **Wave 2**: 6 tasks — T6 → `unspecified-high`, T7-T8 → `deep`, T9 → `unspecified-high`, T10-T11 → `deep`
- **Wave 3**: 5 tasks — T12,T14 → `deep`, T13 → `unspecified-high`, T15-T16 → `quick`
- **Wave 4**: 6 tasks — T17-T21 → `visual-engineering`, T22 → `writing`
- **Final**: 4 tasks — F1 → `oracle`, F2-F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. 프로젝트 스캐폴딩 + pyproject.toml

  **What to do**:
  - `/Users/kimjiwon/Desktop/kimjiwon/ModolRAG/` 에 전체 디렉토리 구조 생성
  - `pyproject.toml` 작성 — name: modolrag, Python 3.11+, 의존성: fastapi, uvicorn, asyncpg, pypdf, pdfplumber, python-docx, openpyxl, python-pptx, httpx, pydantic-settings
  - `modolrag/__init__.py`, `modolrag/main.py` (FastAPI 앱 + static 서빙), `modolrag/config.py` (환경변수 기반 설정)
  - `.gitignore`, `Makefile` (dev, build, test, docker 타겟), `LICENSE` (MIT)
  - `git init` + 초기 커밋

  **Must NOT do**: LangChain/LlamaIndex 의존성 추가, Next.js 관련 파일 생성

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T2-T22
  - **Blocked By**: None

  **References**:
  - `modolrag/main.py` — FastAPI 앱, `StaticFiles` 마운트로 `static/` 서빙
  - Python 패키지 구조: `pyproject.toml` [build-system], [project], [project.scripts] → `modolrag = "modolrag.main:cli"`

  **Acceptance Criteria**:
  - [ ] `pip install -e .` 성공
  - [ ] `python -c "import modolrag"` 에러 없음

  **QA Scenarios**:
  ```
  Scenario: pip install 성공
    Tool: Bash
    Steps:
      1. cd /Users/kimjiwon/Desktop/kimjiwon/ModolRAG
      2. pip install -e ".[dev]"
      3. python -c "import modolrag; print(modolrag.__version__)"
    Expected Result: 버전 문자열 출력, exit code 0
    Evidence: .sisyphus/evidence/task-1-pip-install.txt

  Scenario: 디렉토리 구조 검증
    Tool: Bash
    Steps:
      1. find /Users/kimjiwon/Desktop/kimjiwon/ModolRAG -type f | sort
    Expected Result: modolrag/__init__.py, modolrag/main.py, modolrag/config.py, pyproject.toml, Makefile, LICENSE 존재
    Evidence: .sisyphus/evidence/task-1-structure.txt
  ```

  **Commit**: YES
  - Message: `chore: scaffold ModolRAG project structure`

- [ ] 2. 프로젝트 문서 (README, ARCHITECTURE, SCHEMA)

  **What to do**:
  - `README.md` — 프로젝트 소개, 핵심 특징, 아키텍처 다이어그램(ASCII), 검색 파이프라인, 프로젝트 구조, 빠른 시작, ModolAI 연동 예제, 설계 결정 표
  - `docs/ARCHITECTURE.md` — 상세 아키텍처: 수집 파이프라인 흐름, 검색 파이프라인 흐름, 그래프 구축 과정, RRF 융합 알고리즘, 임베딩 어댑터 패턴, 청킹 전략별 비교, 커뮤니티 감지(k-core)
  - `docs/SCHEMA.md` — 전체 DB 스키마: 테이블 DDL(modolrag_ 프리픽스), 인덱스 전략, 관계 다이어그램, Supabase 호환 노트

  **이 문서의 내용 기반**:
  - 이 플랜의 Context, Work Objectives, 아키텍처 정보 전부 참고
  - 드래프트 파일: `.sisyphus/drafts/rag-strategy.md`
  - 조사 결과의 pgvector 성능 벤치마크, 하이브리드 검색 SQL, 그래프 CTE 패턴

  **Must NOT do**: 코드 파일 작성 (문서만)

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: None (비차단)
  - **Blocked By**: T1

  **Acceptance Criteria**:
  - [ ] README.md 존재, 500줄 이상
  - [ ] docs/ARCHITECTURE.md 존재, 300줄 이상
  - [ ] docs/SCHEMA.md 존재, 200줄 이상

  **QA Scenarios**:
  ```
  Scenario: 문서 존재 확인
    Tool: Bash
    Steps:
      1. wc -l /Users/kimjiwon/Desktop/kimjiwon/ModolRAG/README.md
      2. wc -l /Users/kimjiwon/Desktop/kimjiwon/ModolRAG/docs/ARCHITECTURE.md
      3. wc -l /Users/kimjiwon/Desktop/kimjiwon/ModolRAG/docs/SCHEMA.md
    Expected Result: 각각 500+, 300+, 200+ 줄
    Evidence: .sisyphus/evidence/task-2-docs.txt
  ```

  **Commit**: YES
  - Message: `docs: add README, ARCHITECTURE, SCHEMA documentation`

- [ ] 3. DB 스키마 + 커넥션 모듈

  **What to do**:
  - `modolrag/db/schema.sql` — 전체 DDL:
    - `modolrag_documents` (id UUID, file_name, original_name, file_size, mime_type, category, status enum, extracted_text, chunk_count, embedding_model, uploaded_by, timestamps)
    - `modolrag_document_chunks` (id, document_id FK, content text, embedding halfvec(1536), fts tsvector GENERATED, chunk_index, chunk_level, parent_chunk_id, metadata JSONB)
    - `modolrag_graph_nodes` (id UUID, namespace, title, content, embedding halfvec(1536), node_type, properties JSONB, UNIQUE(namespace,title))
    - `modolrag_graph_edges` (id UUID, namespace, source_id FK, target_id FK, relation_type, weight, context_snippet, metadata JSONB, UNIQUE(namespace,source_id,target_id,relation_type))
    - `modolrag_communities` (id UUID, path ltree, summary, node_ids UUID[], level, embedding halfvec(1536), needs_resummary bool)
    - `modolrag_settings` (id, chunk_size default 512, chunk_overlap default 51, embedding_model default 'nomic-embed-text', embedding_dimensions default 768, similarity_top_k default 5, similarity_threshold default 0.7, response_mode, api_keys JSONB)
    - HNSW 인덱스: `ON modolrag_document_chunks USING hnsw (embedding halfvec_cosine_ops)`
    - GIN 인덱스: `ON modolrag_document_chunks USING gin(fts)`
    - 엣지 양방향 인덱스: source_id, target_id 각각
    - ltree GiST 인덱스: communities.path
  - `modolrag/db/connection.py` — asyncpg 커넥션 풀, POSTGRES_URI 환경변수, 자동 스키마 초기화, pgvector/pg_trgm/ltree 익스텐션 활성화
  - `modolrag/db/migrations/` — 빈 디렉토리 (향후 마이그레이션용)

  **Must NOT do**: 외부 벡터 DB 연결, ORM 사용 (raw SQL)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T6-T14
  - **Blocked By**: T1

  **References**:
  - pgvector 공식: `halfvec(1536)` 타입, `halfvec_cosine_ops` 연산자
  - Supabase 하이브리드 검색: `fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED`
  - 그래프 스키마: `postgres-graph-rag` 패턴 — namespace 기반 멀티테넌시

  **Acceptance Criteria**:
  - [ ] schema.sql 실행 시 에러 없음 (pgvector 익스텐션이 설치된 PostgreSQL에서)
  - [ ] connection.py에서 커넥션 풀 생성 + 쿼리 실행 가능

  **QA Scenarios**:
  ```
  Scenario: 스키마 적용 성공
    Tool: Bash
    Steps:
      1. docker compose up -d postgres (또는 기존 DB 사용)
      2. psql $POSTGRES_URI -f modolrag/db/schema.sql
      3. psql $POSTGRES_URI -c "\dt modolrag_*"
    Expected Result: 6개 테이블 (documents, document_chunks, graph_nodes, graph_edges, communities, settings) 표시
    Evidence: .sisyphus/evidence/task-3-schema.txt

  Scenario: 커넥션 풀 동작
    Tool: Bash
    Steps:
      1. python -c "import asyncio; from modolrag.db.connection import get_pool; asyncio.run(get_pool())"
    Expected Result: 커넥션 풀 생성, exit code 0
    Evidence: .sisyphus/evidence/task-3-connection.txt
  ```

  **Commit**: YES
  - Message: `feat(db): add PostgreSQL schema with pgvector + graph tables`

- [ ] 4. 설정 관리 + API Key 인증 미들웨어

  **What to do**:
  - `modolrag/config.py` 확장 — pydantic-settings 기반: POSTGRES_URI, API_KEYS (콤마 구분), EMBEDDING_PROVIDER (ollama/openai), EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, OLLAMA_BASE_URL, OPENAI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP, SIMILARITY_TOP_K
  - `modolrag/api/auth.py` — FastAPI Dependency: `X-API-Key` 헤더 검증, 설정의 API_KEYS 목록과 대조, 인증 실패 시 401
  - `modolrag/api/middleware.py` — CORS 미들웨어 (ModolAI에서 호출 허용)

  **Must NOT do**: JWT, OAuth, 세션 기반 인증

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T13
  - **Blocked By**: T1

  **Acceptance Criteria**:
  - [ ] 유효한 API Key로 요청 시 200
  - [ ] 잘못된/없는 API Key로 요청 시 401

  **QA Scenarios**:
  ```
  Scenario: 유효한 API Key
    Tool: Bash
    Steps:
      1. API_KEYS=test-key modolrag serve &
      2. curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: test-key" http://localhost:8000/health
    Expected Result: 200
    Evidence: .sisyphus/evidence/task-4-auth-valid.txt

  Scenario: 잘못된 API Key
    Tool: Bash
    Steps:
      1. curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: wrong" http://localhost:8000/health
    Expected Result: 401
    Evidence: .sisyphus/evidence/task-4-auth-invalid.txt
  ```

  **Commit**: YES
  - Message: `feat(auth): add API key authentication middleware`

- [ ] 5. 임베딩 어댑터 (Ollama + OpenAI)

  **What to do**:
  - `modolrag/core/embedder.py` — 어댑터 패턴:
    - `EmbedderBase` (ABC): `embed(text) -> list[float]`, `embed_batch(texts) -> list[list[float]]`
    - `OllamaEmbedder`: httpx로 `{OLLAMA_BASE_URL}/api/embeddings` 호출, 모델명 설정 가능
    - `OpenAIEmbedder`: httpx로 `https://api.openai.com/v1/embeddings` 호출, API Key 설정
    - `get_embedder(config) -> EmbedderBase` 팩토리 함수
    - 배치 처리: 대량 텍스트를 일정 크기로 나눠 임베딩, rate limit 대응
    - 차원 수 자동 감지 (첫 호출 시 결과에서 읽음)

  **Must NOT do**: sentence-transformers 로컬 추론, HuggingFace 직접 호출

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T7, T8, T14
  - **Blocked By**: T1

  **Acceptance Criteria**:
  - [ ] OllamaEmbedder: nomic-embed-text로 768차원 벡터 반환 (Ollama 실행 시)
  - [ ] OpenAIEmbedder: text-embedding-3-small로 1536차원 벡터 반환 (API Key 있을 시)
  - [ ] 배치 임베딩 동작

  **QA Scenarios**:
  ```
  Scenario: Ollama 임베딩 (Ollama 미실행 시 스킵)
    Tool: Bash
    Steps:
      1. python -c "
         from modolrag.core.embedder import OllamaEmbedder
         e = OllamaEmbedder(base_url='http://localhost:11434', model='nomic-embed-text')
         import asyncio
         result = asyncio.run(e.embed('hello world'))
         print(f'dims={len(result)}')
         assert len(result) == 768
         "
    Expected Result: dims=768
    Evidence: .sisyphus/evidence/task-5-ollama.txt

  Scenario: 팩토리 함수
    Tool: Bash
    Steps:
      1. python -c "
         from modolrag.core.embedder import get_embedder
         from modolrag.config import Settings
         s = Settings(EMBEDDING_PROVIDER='ollama')
         e = get_embedder(s)
         print(type(e).__name__)
         "
    Expected Result: OllamaEmbedder
    Evidence: .sisyphus/evidence/task-5-factory.txt
  ```

  **Commit**: YES
  - Message: `feat(embed): add Ollama + OpenAI embedding adapters`

- [ ] 6. 문서 파서 6종

  **What to do**:
  - `modolrag/parsers/base.py` — `ParserBase(ABC)`: `parse(file_path) -> ParsedDocument(text, metadata, pages[])`
  - `modolrag/parsers/pdf.py` — pypdf(BSD-3) + pdfplumber(MIT): 텍스트 추출 + 테이블 감지. 전부 기본 설치, 선택지 없음
  - `modolrag/parsers/docx.py` — python-docx(MIT): 텍스트+스타일+헤딩 구조
  - `modolrag/parsers/xlsx.py` — openpyxl(MIT): 시트별 텍스트, 셀 데이터 마크다운 테이블로 변환
  - `modolrag/parsers/pptx.py` — python-pptx(MIT): 슬라이드별 텍스트+노트
  - `modolrag/parsers/markdown.py` — 마크다운 파싱, 프론트매터(YAML) 추출, 섹션 분리
  - `modolrag/parsers/text.py` — 플레인텍스트 (인코딩 자동 감지)
  - `modolrag/parsers/__init__.py` — `get_parser(mime_type) -> ParserBase` 팩토리

  **설계 원칙**: 플러그인 시스템 없음, extras 없음. `pip install modolrag` 하면 모든 파서가 즉시 동작. 파서 확장(docling 등)은 v2에서 사용자 요청 시 검토.

  **Must NOT do**: OCR (v1 스코프 외), 웹 크롤링, **AGPL/GPL 라이선스 파서 (pymupdf, marker-pdf)**

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T14
  - **Blocked By**: T3

  **Acceptance Criteria**:
  - [ ] 각 파서가 ParsedDocument 반환
  - [ ] PDF에서 텍스트+페이지수 정상 추출
  - [ ] DOCX에서 헤딩 구조 유지

  **QA Scenarios**:
  ```
  Scenario: PDF 파싱
    Tool: Bash
    Steps:
      1. python -c "
         from modolrag.parsers import get_parser
         parser = get_parser('application/pdf')
         result = parser.parse('tests/fixtures/sample.pdf')
         print(f'pages={len(result.pages)}, text_len={len(result.text)}')
         assert len(result.text) > 0
         "
    Expected Result: pages>0, text_len>0
    Evidence: .sisyphus/evidence/task-6-pdf.txt
  ```

  **Commit**: YES
  - Message: `feat(parsers): add document parsers (PDF/DOCX/XLSX/PPTX/MD/TXT)`

- [ ] 7. 청킹 엔진

  **What to do**:
  - `modolrag/core/chunker.py`:
    - `RecursiveChunker(chunk_size=512, overlap=51)` — 구분자 계층: `\n\n` → `\n` → `. ` → ` ` → 문자
    - `SemanticChunker(embedder, threshold=0.5)` — 문장 임베딩 유사도 기반 분할
    - `PageChunker()` — 페이지 단위 (PDF 전용)
    - `get_chunker(strategy, config) -> ChunkerBase` 팩토리
    - 모든 청커: Parent-Child 패턴 지원 (큰 청크 → 작은 청크, parent_chunk_id 링크)
    - 청크 메타데이터: document_id, chunk_index, chunk_level, source_page

  **Must NOT do**: AST 코드 청킹 (v1 스코프 외)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T14
  - **Blocked By**: T3, T5

  **Acceptance Criteria**:
  - [ ] RecursiveChunker: 1000자 텍스트 → 2-3개 청크, 오버랩 존재
  - [ ] Parent-Child: parent 청크와 child 청크가 올바르게 링크됨

  **QA Scenarios**:
  ```
  Scenario: Recursive 청킹
    Tool: Bash
    Steps:
      1. python -c "
         from modolrag.core.chunker import RecursiveChunker
         c = RecursiveChunker(chunk_size=100, overlap=10)
         chunks = c.chunk('A' * 250)
         print(f'count={len(chunks)}')
         assert len(chunks) >= 2
         "
    Expected Result: count>=2
    Evidence: .sisyphus/evidence/task-7-recursive.txt
  ```

  **Commit**: YES
  - Message: `feat(chunker): add recursive/semantic/page chunking engine`

- [ ] 8. 벡터 스토어 (pgvector CRUD + HNSW)

  **What to do**:
  - `modolrag/core/vector_store.py`:
    - `upsert_chunks(document_id, chunks_with_embeddings)` — INSERT ... ON CONFLICT DO UPDATE
    - `search_similar(query_embedding, top_k=20, threshold=0.7)` — `ORDER BY embedding <=> $1 LIMIT $2`
    - `delete_by_document(document_id)` — 문서 삭제 시 관련 청크 삭제
    - `get_chunk_by_id(chunk_id)` — 단일 청크 조회
    - 모든 쿼리는 asyncpg 사용, halfvec 타입 지원

  **Must NOT do**: 인메모리 벡터 검색, FAISS, LanceDB

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T12
  - **Blocked By**: T3, T5

  **Acceptance Criteria**:
  - [ ] upsert 후 search_similar로 결과 반환
  - [ ] cosine 유사도 순서 정렬 확인
  - [ ] delete_by_document로 청크 제거 확인

  **QA Scenarios**:
  ```
  Scenario: 벡터 CRUD + 검색
    Tool: Bash
    Steps:
      1. pytest tests/test_vector_store.py -v
    Expected Result: 3 tests passed
    Evidence: .sisyphus/evidence/task-8-vector.txt
  ```

  **Commit**: YES
  - Message: `feat(vector): add pgvector store with HNSW search`

- [ ] 9. 전문 검색 (tsvector + GIN)

  **What to do**:
  - `modolrag/core/fts.py`:
    - `search_fts(query_text, top_k=20)` — `WHERE fts @@ websearch_to_tsquery($1) ORDER BY ts_rank_cd(fts, ...) DESC`
    - tsvector 칼럼은 GENERATED 이므로 별도 업데이트 불필요
    - 한국어 지원: `to_tsvector('simple', content)` 폴백 (korean full-text는 별도 익스텐션 필요)
    - 검색 결과에 BM25 근사 점수 포함 (ts_rank_cd + normalization=32)

  **Must NOT do**: ParadeDB pg_search, Elasticsearch

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T12
  - **Blocked By**: T3

  **Acceptance Criteria**:
  - [ ] 키워드 검색 시 관련 청크 반환
  - [ ] ts_rank 점수 포함

  **QA Scenarios**:
  ```
  Scenario: FTS 검색
    Tool: Bash
    Steps:
      1. pytest tests/test_fts.py -v
    Expected Result: tests passed
    Evidence: .sisyphus/evidence/task-9-fts.txt
  ```

  **Commit**: YES
  - Message: `feat(fts): add full-text search with tsvector + GIN`

- [ ] 10. 그래프 스토어 (노드/엣지 CRUD + CTE 탐색)

  **What to do**:
  - `modolrag/core/graph_store.py`:
    - `upsert_node(namespace, title, content, embedding, node_type, properties)` — ON CONFLICT DO UPDATE
    - `upsert_edge(namespace, source_id, target_id, relation_type, weight, context_snippet)` — ON CONFLICT: weight += 1
    - `traverse_graph(seed_node_ids, max_depth=2, namespace)` — Recursive CTE, 양방향, 사이클 방지 (ARRAY path)
    - `get_neighbors(node_id, namespace)` — 1홉 이웃
    - `search_nodes_by_embedding(query_embedding, top_k, namespace)` — 노드 벡터 검색
    - `link_chunks_to_entities(chunk_id, entity_ids)` — chunk_entities 조인테이블 관리
    - `get_graph_data(namespace)` — 시각화용 전체 노드/엣지 반환

  **Must NOT do**: Neo4j, NetworkX (순수 SQL), 3홉 이상 탐색

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T11, T12
  - **Blocked By**: T3, T5

  **References**:
  - `postgres-graph-rag` Recursive CTE 패턴: `WITH RECURSIVE graph_expansion AS (... WHERE ge.depth < $3 AND NOT (n.id = ANY(ge.visited)))`
  - 엣지 weight 누적: `ON CONFLICT DO UPDATE SET weight = edges.weight + 1.0`

  **Acceptance Criteria**:
  - [ ] 노드 업서트 + 엣지 업서트 동작
  - [ ] 2홉 탐색: A→B→C 관계에서 A의 시드로 C 도달 확인
  - [ ] 사이클 A→B→A에서 무한루프 방지 확인

  **QA Scenarios**:
  ```
  Scenario: 그래프 탐색 2홉
    Tool: Bash
    Steps:
      1. pytest tests/test_graph_store.py -v
    Expected Result: tests passed (탐색, 사이클방지, 양방향)
    Evidence: .sisyphus/evidence/task-10-graph.txt
  ```

  **Commit**: YES
  - Message: `feat(graph): add graph store with recursive CTE traversal`

- [ ] 11. LLM 엔티티/관계 추출기

  **What to do**:
  - `modolrag/core/extractor.py`:
    - `extract_entities_and_relations(text, llm_endpoint, model)` — LLM 호출로 JSON 트리플 추출
    - 2-pass: 추출 → 검증 프롬프트
    - 출력 형식: `{"entities": [{"name","type","description"}], "relationships": [{"subject","predicate","object","confidence"}]}`
    - entity_type: PERSON, ORG, CONCEPT, LOCATION, EVENT
    - 신뢰도: 1.0=명시적, 0.7=강하게 암시, 0.5=추론
    - LLM 호출: 기존 ModolAI 모델서버 또는 직접 Ollama/OpenAI API (httpx)
    - 마크다운 `[[wikilink]]` 패턴 자동 감지 → relation_type='explicitly_linked'

  **Must NOT do**: spaCy NER, 룰 기반 추출 (LLM만 사용)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T14
  - **Blocked By**: T10, T5

  **References**:
  - 2-pass 추출 프롬프트: PingCAP 패턴 (EXTRACTION_PROMPT → VERIFICATION_PROMPT)
  - 엔티티 중복제거: `pg_trgm similarity > 0.7 AND embedding cosine < 0.15`

  **Acceptance Criteria**:
  - [ ] 텍스트 입력 → entities + relationships JSON 반환
  - [ ] `[[wikilink]]` 감지 동작

  **QA Scenarios**:
  ```
  Scenario: 엔티티 추출 (LLM 필요)
    Tool: Bash
    Steps:
      1. python -c "
         from modolrag.core.extractor import extract_entities_and_relations
         import asyncio
         result = asyncio.run(extract_entities_and_relations(
           'Apple was founded by Steve Jobs in Cupertino.',
           llm_endpoint='http://localhost:11434/api/chat',
           model='llama3'
         ))
         print(f'entities={len(result.entities)}, rels={len(result.relationships)}')
         assert len(result.entities) >= 2
         "
    Expected Result: entities>=2 (Apple, Steve Jobs), rels>=1 (founded)
    Evidence: .sisyphus/evidence/task-11-extract.txt
  ```

  **Commit**: YES
  - Message: `feat(extract): add LLM entity/relationship extraction`

- [ ] 12. 하이브리드 검색 + RRF 융합

  **What to do**:
  - `modolrag/core/hybrid_search.py`:
    - `hybrid_search(query_text, query_embedding, top_k=10, mode='hybrid', namespace='default')`:
      - mode='vector': 벡터 검색만
      - mode='fts': 전문 검색만
      - mode='graph': 그래프 탐색만
      - mode='hybrid': 3개 모두 → RRF 융합
    - RRF 융합: `score = Σ 1/(k + rank_i)`, k=60
    - 그래프 확장: 벡터 검색 시드 → graph_store.traverse_graph(2홉) → 관련 청크 수집
    - 그래프 결과 가중치: `score * (0.8 ** hop_depth)`
    - 결과 형식: `[{chunk_id, content, score, source_document, match_type}]`

  **Must NOT do**: 외부 검색 엔진 (Elasticsearch, Meilisearch)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (Sequential)
  - **Blocks**: T13, T14
  - **Blocked By**: T8, T9, T10

  **References**:
  - Supabase 공식 hybrid_search SQL 함수 패턴
  - RRF 구현: DEV.to 프로덕션 예제 (k=60, FULL OUTER JOIN)

  **Acceptance Criteria**:
  - [ ] hybrid 모드: 벡터+FTS+그래프 3개 결과 융합
  - [ ] 각 모드 개별 동작
  - [ ] RRF 점수 정렬 정확성

  **QA Scenarios**:
  ```
  Scenario: 하이브리드 검색
    Tool: Bash
    Steps:
      1. pytest tests/test_hybrid_search.py -v
    Expected Result: tests passed
    Evidence: .sisyphus/evidence/task-12-hybrid.txt
  ```

  **Commit**: YES
  - Message: `feat(search): add hybrid search with RRF fusion`

- [ ] 13. FastAPI 라우터 통합

  **What to do**:
  - `modolrag/api/ingest.py`:
    - `POST /api/ingest` — 파일 업로드(multipart), 비동기 처리 시작, document_id + status 반환
    - `GET /api/documents` — 문서 목록 (pagination, status 필터)
    - `GET /api/documents/{id}` — 문서 상세 + 청크 수 + 처리 상태
    - `DELETE /api/documents/{id}` — 문서 + 청크 + 그래프 노드 삭제
  - `modolrag/api/search.py`:
    - `POST /api/search` — `{query, top_k, mode, namespace}` → hybrid_search 호출
  - `modolrag/api/graph.py`:
    - `GET /api/graph` — 전체 노드/엣지 데이터 (시각화용)
    - `GET /api/graph/node/{id}` — 노드 상세 + 이웃
  - `modolrag/api/admin.py`:
    - `GET /api/settings` — 현재 설정
    - `PUT /api/settings` — 설정 업데이트
    - `GET /health` — 헬스체크
  - `modolrag/main.py` 업데이트 — 모든 라우터 등록, 에러 핸들러

  **Must NOT do**: WebSocket, GraphQL

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: T14
  - **Blocked By**: T4, T12

  **Acceptance Criteria**:
  - [ ] 모든 엔드포인트 curl 테스트 통과
  - [ ] OpenAPI 문서 /docs에서 확인 가능

  **QA Scenarios**:
  ```
  Scenario: API 엔드포인트 동작
    Tool: Bash
    Steps:
      1. curl -s http://localhost:8000/docs | grep "openapi"
      2. curl -s -w "%{http_code}" -H "X-API-Key: test" http://localhost:8000/health
      3. curl -s -w "%{http_code}" -H "X-API-Key: test" http://localhost:8000/api/documents
    Expected Result: openapi 문서 존재, health=200, documents=200
    Evidence: .sisyphus/evidence/task-13-api.txt
  ```

  **Commit**: YES
  - Message: `feat(api): integrate FastAPI routers`

- [ ] 14. 수집 파이프라인 (E2E)

  **What to do**:
  - `modolrag/core/pipeline.py`:
    - `ingest_document(file_path, settings)` — 전체 파이프라인:
      1. 파서 선택 (mime_type 기반)
      2. 문서 파싱 → ParsedDocument
      3. 청킹 → chunks[]
      4. 임베딩 생성 → chunks_with_embeddings[]
      5. DB 저장 (vector_store.upsert_chunks)
      6. 엔티티/관계 추출 (extractor)
      7. 그래프 노드/엣지 저장 (graph_store.upsert_*)
      8. 문서 상태 업데이트 (processing → indexed)
    - 비동기 실행 (BackgroundTasks 또는 asyncio.create_task)
    - 에러 핸들링: 각 단계별 실패 시 status='error' + 에러 메시지 저장
    - 진행률 추적: vectorization_progress 0-100%

  **Must NOT do**: Celery, Redis Queue (v1은 인프로세스 비동기)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: T15, T16
  - **Blocked By**: T6, T7, T11, T13

  **Acceptance Criteria**:
  - [ ] PDF 업로드 → 파싱 → 청킹 → 임베딩 → DB 저장 → 그래프 빌드 전체 동작
  - [ ] 검색으로 수집한 문서 내용 검색 가능

  **QA Scenarios**:
  ```
  Scenario: E2E 수집 + 검색
    Tool: Bash
    Steps:
      1. curl -X POST http://localhost:8000/api/ingest -H "X-API-Key: test" -F "file=@tests/fixtures/sample.pdf"
      2. sleep 10  # 처리 대기
      3. curl http://localhost:8000/api/documents -H "X-API-Key: test" | python -m json.tool
      4. curl -X POST http://localhost:8000/api/search -H "X-API-Key: test" -H "Content-Type: application/json" -d '{"query":"test","top_k":3,"mode":"hybrid"}'
    Expected Result: 문서 status=indexed, 검색 결과 1개 이상
    Evidence: .sisyphus/evidence/task-14-e2e.txt
  ```

  **Commit**: YES
  - Message: `feat(pipeline): add end-to-end ingestion pipeline`

- [ ] 15. CLI 엔트리포인트

  **What to do**:
  - `modolrag/cli.py`:
    - `modolrag serve` — uvicorn 서버 기동 (--host, --port, --db, --reload 옵션)
    - `modolrag init-db` — 스키마 초기화
    - `modolrag ingest <file>` — CLI에서 직접 문서 수집
  - `pyproject.toml` [project.scripts] 등록

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: T14

  **Acceptance Criteria**:
  - [ ] `modolrag serve --help` 동작
  - [ ] `modolrag init-db` 스키마 적용

  **Commit**: YES
  - Message: `feat(cli): add modolrag serve CLI entry point`

- [ ] 16. Docker Compose + Makefile

  **What to do**:
  - `docker-compose.yml`: PostgreSQL 15 (pgvector 확장) + ModolRAG 서비스, 볼륨 마운트, 헬스체크
  - `Dockerfile`: Python 3.11 slim, pip install, uvicorn 실행
  - `Makefile` 업데이트: `make dev`, `make build`, `make docker-up`, `make docker-down`, `make test`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: None
  - **Blocked By**: T14

  **Acceptance Criteria**:
  - [ ] `docker compose up -d` 성공
  - [ ] `curl http://localhost:8000/health` → 200

  **Commit**: YES
  - Message: `chore(docker): add Docker Compose + Makefile`

- [ ] 17. 대시보드 스캐폴딩

  **What to do**:
  - `dashboard/` — Vite + React + TypeScript + Tailwind CSS 프로젝트 초기화
  - 라우팅: react-router-dom (Documents, Search, Graph, Settings)
  - 레이아웃: 사이드바 네비게이션 + 메인 콘텐츠
  - API 클라이언트: fetch 래퍼 (X-API-Key 자동 포함)
  - `vite.config.ts`: 빌드 outDir → `../modolrag/static/`
  - package.json scripts: dev, build, preview

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocks**: T18-T21
  - **Blocked By**: T1

  **Commit**: YES (T17-T21 함께)
  - Message: `feat(dashboard): add React SPA dashboard with graph visualization`

- [ ] 18. Documents 페이지

  **What to do**:
  - 파일 업로드 (드래그&드롭 + 클릭), 진행률 표시
  - 문서 목록 테이블 (이름, 타입, 상태 배지, 청크 수, 날짜)
  - 상태 폴링 (processing → indexed)
  - 문서 삭제 확인 모달
  - 빈 상태 UI

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocked By**: T17, T13

- [ ] 19. Search 페이지

  **What to do**:
  - 검색 입력 (쿼리, top_k 슬라이더, mode 선택: vector/fts/graph/hybrid)
  - 검색 결과 카드 (content, score 바, source document, match_type 배지)
  - 검색 소요 시간 표시
  - 빈 결과 UI

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocked By**: T17, T13

- [ ] 20. Graph 페이지

  **What to do**:
  - `react-force-graph-2d` 또는 `react-force-graph-3d`로 노드/엣지 시각화
  - 노드: 색상=node_type별, 크기=연결 수 비례
  - 엣지: 두께=weight 비례, 라벨=relation_type
  - 노드 클릭 → 상세 패널 (content, properties, 이웃 목록)
  - 네임스페이스 필터
  - 줌/팬 컨트롤

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocked By**: T17, T13

- [ ] 21. Settings 페이지 + 대시보드 빌드

  **What to do**:
  - Settings 페이지: 청킹 설정(size, overlap), 임베딩 설정(provider, model), 검색 설정(top_k, threshold), API Key 관리
  - `npm run build` → `modolrag/static/` 에 빌드 산출물 복사
  - `modolrag/main.py` 에서 static 마운트 확인

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocked By**: T17, T13

  **Acceptance Criteria** (T17-T21 통합):
  - [ ] `http://localhost:8000/dashboard` 에서 React SPA 로드
  - [ ] 4개 페이지 정상 네비게이션
  - [ ] Documents: 파일 업로드 동작
  - [ ] Search: 검색 결과 표시
  - [ ] Graph: 노드/엣지 시각화
  - [ ] Settings: 설정 저장 동작

  **QA Scenarios**:
  ```
  Scenario: 대시보드 E2E
    Tool: Playwright
    Steps:
      1. goto http://localhost:8000/dashboard
      2. assert title contains "ModolRAG"
      3. click sidebar "Documents" → assert URL contains /documents
      4. click sidebar "Search" → assert URL contains /search
      5. click sidebar "Graph" → assert canvas element exists
      6. click sidebar "Settings" → assert form elements exist
      7. screenshot each page
    Expected Result: 4개 페이지 정상 렌더링
    Evidence: .sisyphus/evidence/task-21-dashboard-*.png
  ```

  **Commit**: YES
  - Message: `feat(dashboard): add React SPA dashboard with graph visualization`

- [ ] 22. ModolAI 연동 가이드 문서

  **What to do**:
  - `docs/MODOLAI_INTEGRATION.md`:
    - ModolAI completions API에서 ModolRAG 호출하는 코드 예제
    - 환경변수 설정 가이드 (MODOLRAG_URL, MODOLRAG_API_KEY)
    - Docker 네트워크 설정 (docker-compose.yml 예제)
    - 관리자 설정 UI에서 RAG 토글 추가하는 방법
    - 트러블슈팅 (연결 실패, 타임아웃, 임베딩 모델 불일치)

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocked By**: T14

  **Commit**: YES
  - Message: `docs: add ModolAI integration guide`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `ruff check`, `mypy`, `pytest`. Review all Python files for: type hints, docstrings, error handling. Check for hardcoded secrets, unused imports, bare excepts. Verify pyproject.toml metadata.
  Output: `Lint [PASS/FAIL] | Types [PASS/FAIL] | Tests [N pass/N fail] | VERDICT`

- [ ] F3. **E2E QA** — `unspecified-high` + `playwright` skill
  Start from clean state. docker compose up. Upload a PDF via /api/ingest. Wait for processing. Search via /api/search. Verify graph data via /api/graph. Open dashboard, navigate all 4 pages, test upload + search + graph view. Save screenshots.
  Output: `API [N/N pass] | Dashboard [N/N] | Integration [N/N] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read spec, read actual code. Verify 1:1 — everything in spec was built, nothing beyond spec was built. Check "Must NOT do" compliance. Detect unaccounted changes.
  Output: `Tasks [N/N compliant] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- T1: `chore: scaffold ModolRAG project structure`
- T2: `docs: add README, ARCHITECTURE, SCHEMA documentation`
- T3: `feat(db): add PostgreSQL schema with pgvector + graph tables`
- T4: `feat(auth): add API key authentication middleware`
- T5: `feat(embed): add Ollama + OpenAI embedding adapters`
- T6: `feat(parsers): add document parsers (PDF/DOCX/XLSX/PPTX/MD/TXT)`
- T7: `feat(chunker): add recursive/semantic/page chunking engine`
- T8: `feat(vector): add pgvector store with HNSW search`
- T9: `feat(fts): add full-text search with tsvector + GIN`
- T10: `feat(graph): add graph store with recursive CTE traversal`
- T11: `feat(extract): add LLM entity/relationship extraction`
- T12: `feat(search): add hybrid search with RRF fusion`
- T13: `feat(api): integrate FastAPI routers (ingest/search/graph/admin)`
- T14: `feat(pipeline): add end-to-end ingestion pipeline`
- T15: `feat(cli): add modolrag serve CLI entry point`
- T16: `chore(docker): add Docker Compose + Makefile`
- T17-T21: `feat(dashboard): add React SPA dashboard with graph visualization`
- T22: `docs: add ModolAI integration guide`

---

## Success Criteria

### Verification Commands
```bash
# 설치
pip install -e .  # Expected: Successfully installed modolrag

# 서버 기동
modolrag serve --db $POSTGRES_URI  # Expected: Uvicorn running on 0.0.0.0:8000

# 문서 수집
curl -X POST http://localhost:8000/api/ingest \
  -H "X-API-Key: test-key" \
  -F "file=@test.pdf"  # Expected: 200, {"document_id": "...", "status": "processing"}

# 검색
curl -X POST http://localhost:8000/api/search \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5, "mode": "hybrid"}'
  # Expected: 200, {"results": [...], "mode": "hybrid"}

# 그래프
curl http://localhost:8000/api/graph \
  -H "X-API-Key: test-key"
  # Expected: 200, {"nodes": [...], "edges": [...]}

# Docker
docker compose up -d  # Expected: modolrag + postgres containers running
curl http://localhost:8000/health  # Expected: 200, {"status": "ok"}

# 대시보드
# http://localhost:8000/dashboard → React SPA loads
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] pip install 성공
- [ ] Docker Compose 실행 성공
- [ ] 문서 수집 E2E 동작
- [ ] 하이브리드 검색 동작
- [ ] 그래프 시각화 동작
- [ ] 대시보드 4개 페이지 정상

---

## Work Log

> 모든 작업 과정을 누적 기록. 최신 항목이 위에 위치.

### 2026-03-17 — Swagger/Docker 보강 (v0.4)

**배경**: API 문서 자동화(Swagger), Docker 인프라, 대시보드 연동 보강 필요.

**변경 사항**:

1. **Dockerfile 멀티스테이지 빌드**
   - Stage 1: Node.js 20 → dashboard `npm run build` → modolrag/static/ 출력
   - Stage 2: Python 3.11-slim → pip install → 대시보드 static 복사
   - 헬스체크: httpx → curl 변경 (더 가벼움)
   - `.dockerignore` 업데이트 (node_modules, tests, .git 제외)

2. **docker-compose.yml 강화**
   - Ollama 서비스 추가 (ollama/ollama:latest, 볼륨, 헬스체크, GPU 옵션 주석)
   - 환경변수 기본값 패턴: `${POSTGRES_PASSWORD:-modolrag}`, `${MODOLRAG_PORT:-8000}`
   - 3개 서비스: postgres (pgvector:pg15) + ollama + modolrag
   - 사용법 주석 추가 (Ollama 없이 실행, 모델 다운로드 등)

3. **OpenAPI/Swagger 보강**
   - FastAPI 메타데이터: summary, rich description (features, auth, dashboard 링크), license_info
   - 4개 태그 카테고리 + 상세 설명: documents, search, graph, admin
   - Pydantic response 모델: IngestResponse, DocumentListResponse, DocumentResponse, SearchResponse, SearchResultItem
   - 모든 요청/응답에 Field() 설명, validation 제약, json_schema_extra 예제
   - 전 엔드포인트 summary + 상세 docstring (파이프라인 설명, 모드 설명 등)
   - Health 엔드포인트: /docs, /redoc, /dashboard 링크 반환

4. **대시보드 사이드바 API 링크**
   - "API" 섹션 추가: Swagger UI (/docs) + ReDoc (/redoc) 외부 링크
   - 대시보드에서 바로 API 문서 접근 가능

**API 현황 (11개 엔드포인트)**:
| Method | Path | Tag | Summary |
|---|---|---|---|
| GET | /health | admin | Health check |
| GET | /api/settings | admin | Get settings |
| PUT | /api/settings | admin | Update settings |
| POST | /api/ingest | documents | Upload a document |
| GET | /api/documents | documents | List documents |
| GET | /api/documents/{id} | documents | Get document details |
| DELETE | /api/documents/{id} | documents | Delete a document |
| POST | /api/search | search | Hybrid search |
| GET | /api/graph | graph | Get knowledge graph |
| GET | /api/graph/node/{id} | graph | Get node details |
| MOUNT | /dashboard | — | React SPA |

**자동 생성 문서 URL**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

### 2026-03-17 — 전체 구현 완료 (v0.3)

**배경**: 전략 문서 v0.2 기반으로 전체 프로젝트 구현 시작. 4 Wave 병렬 실행.

**실행 방식**:
- Wave 1 (T1-T5): T1 선행 후 T2-T5 병렬
- Wave 2 (T6-T11): T6-T10 병렬, T11은 T10 완료 후
- Wave 3 (T12-T16): T12 선행 후 T13 → T14 + T15 + T16 병렬
- Wave 4 (T17-T22): T17-T21(대시보드) + T2(문서 재시도) + T22 병렬

**산출물 (커밋 3개, 65+ files, 8,000+ lines)**:

| 커밋 | 내용 | 파일 |
|---|---|---|
| `4ba3db8` | 프로젝트 스캐폴딩 | 20 files |
| `61acb2c` | 전체 구현 (백엔드 + 대시보드 + 문서) | 65 files, +8,122 lines |
| `b0024e3` | Swagger/Docker 보강 | 9 files, +261/-66 lines |

**구현 완료 모듈**:

1. **코어 엔진** (8 모듈):
   - `embedder.py` — Ollama + OpenAI 어댑터, 팩토리 패턴, 배치 처리
   - `chunker.py` — RecursiveChunker, SemanticChunker, PageChunker + 팩토리
   - `vector_store.py` — pgvector CRUD, HNSW 코사인 검색, halfvec 포맷팅
   - `fts.py` — tsvector + GIN, websearch_to_tsquery, ts_rank_cd(BM25 근사)
   - `graph_store.py` — 노드/엣지 CRUD, 2홉 BFS CTE, 양방향 탐색, 사이클 방지
   - `hybrid_search.py` — RRF 융합 (k=60), 4가지 모드 (vector/fts/graph/hybrid)
   - `extractor.py` — LLM 엔티티/관계 추출, 위키링크 감지, JSON 파싱 (코드블록 허용)
   - `pipeline.py` — E2E 파이프라인 (parse→chunk→embed→store→extract→graph), 진행률 추적, 에러 핸들링

2. **API** (6 파일, 11 엔드포인트 + Swagger/ReDoc):
   - `auth.py` — X-API-Key 검증 (미설정시 전체 허용)
   - `middleware.py` — CORS (전체 허용)
   - `ingest.py` — 문서 업로드 + BackgroundTask 파이프라인 연동
   - `search.py` — 하이브리드 검색 (쿼리 임베딩 → 3중 검색 → RRF)
   - `graph.py` — 그래프 데이터 + 노드 상세 (이웃 포함)
   - `admin.py` — 헬스체크 + 설정 CRUD

3. **파서** (6종):
   - PDF (pypdf + pdfplumber), DOCX (python-docx), XLSX (openpyxl), PPTX (python-pptx), Markdown (YAML 프론트매터), Text (인코딩 자동감지)
   - 모든 파서 MIT/BSD 라이선스 ✅

4. **DB** (6 테이블, 8 인덱스):
   - schema.sql: documents, chunks(halfvec+tsvector), graph_nodes, graph_edges, communities, settings
   - connection.py: asyncpg 풀, halfvec 코덱, 스키마 자동 초기화

5. **대시보드** (React SPA, 4 페이지):
   - Documents: 업로드(드래그앤드롭), 목록(상태 배지), 삭제, 자동 새로고침
   - Search: 쿼리 입력, 모드 선택기, Top-K 슬라이더, 결과 카드
   - Graph: react-force-graph-2d, 노드 타입별 색상, 클릭 상세, 범례
   - Settings: 폼 필드(chunk_size, threshold 등), API Key(localStorage), 저장 피드백

6. **인프라**:
   - CLI: serve, init-db, ingest 커맨드 (argparse + uvicorn)
   - Docker: 멀티스테이지 빌드 (Node→Python), pgvector:pg15 + Ollama + ModolRAG
   - Makefile: dev, build, test, lint, format, docker-up/down/build/logs

7. **문서** (4 파일, 740줄):
   - README.md (226줄): 아키텍처도, Quick Start, 설정, 프로젝트 구조, 설계 결정
   - docs/ARCHITECTURE.md (174줄): 파이프라인, RRF 공식, Graph CTE, 임베딩 어댑터
   - docs/SCHEMA.md (190줄): 6 테이블 DDL, 인덱스 전략, ER 다이어그램
   - docs/MODOLAI_INTEGRATION.md (150줄): 연동 아키텍처, 코드 예제, Docker 네트워크, 트러블슈팅

**검증 결과**:
- ✅ `pip install -e .` 성공 (python3.11)
- ✅ 전체 모듈 트리 import 통과 (15 routes registered)
- ✅ RecursiveChunker, PageChunker 테스트 통과
- ✅ RRF 융합 테스트 통과
- ✅ Wikilink 추출 테스트 통과
- ✅ 대시보드 빌드 성공 (182ms)
- ✅ OpenAPI 태그 4개, response 모델 적용 확인

---

### 2026-03-17 — 전략 문서 보강 (v0.2)

**배경**: 기존 오픈소스 RAG 생태계 대비 ModolRAG 전략 분석 수행. 8개 경쟁 프로젝트(RAGFlow, LightRAG, R2R, Kotaemon, GraphRAG, Cognee, AnythingLLM, Verba) + pgvector 프로덕션 벤치마크 + ModolAI 기존 코드베이스 분석.

**리서치 결과 요약**:
- R2R(SciPhi)이 동일 아키텍처(PG+pgvector+FTS+RRF+FastAPI)로 가장 직접적 경쟁자였으나 2025.06 이후 개발 중단
- RAGFlow(75K⭐)이 시장 리더이나 Docker 5+컨테이너로 무거움
- pgvector는 50M 벡터까지 Pinecone급 성능 (pgvectorscale DiskANN 기준)
- PostgreSQL CTE 그래프 탐색이 Apache AGE 대비 250x 빠름 (2홉 기준)

**변경 사항**:
1. **🚨 라이선스 블로커 발견 및 수정**
   - pymupdf(PyMuPDF)가 **AGPL-3.0** — MIT 프로젝트와 호환 불가
   - pymupdf → pypdf(BSD) + pdfplumber(MIT)로 교체
   - marker-pdf(GPL-3.0)도 금지 목록에 추가
   - `License Compliance` 섹션 신설 — 허용/금지 의존성 명시

2. **경쟁 포지셔닝 섹션 추가** (`Competitive Positioning`)
   - 시장 포지셔닝 맵 (기능 완전 × 인프라 경량)
   - R2R 빈자리 분석 — 동일 스택, 9개월 릴리즈 중단
   - 경쟁자 6개 프로젝트별 차별점 테이블
   - 안티-타겟 명시 (문서 파싱 최강, 비개발자 시장, 학술 그래프 RAG)

3. **Graph RAG 차별화 섹션 추가** (`Graph RAG Differentiation`)
   - MS GraphRAG / LightRAG / ModolRAG 3자 비교 테이블
   - "같은 DB, 같은 트랜잭션" 핵심 메시지
   - PostgreSQL CTE 벤치마크 데이터 (0.09ms @ 10K nodes)

4. **ModolAI 연동 브릿지 섹션 추가** (`ModolAI Integration Bridge`)
   - 기존 rag_*/chat_files 테이블 ↔ modolrag_* 테이블 매핑
   - 3단계 마이그레이션 (공존 → 마이그레이션 도구 → 네이티브 통합)
   - 기존 /v1/embeddings, /v1/rerank 엔드포인트 재활용 설계

5. **파서 아키텍처 심플화**
   - 초기 과설계(3백엔드 플러그인) → 단일 네이티브 파서로 복원
   - `pip install modolrag` 하면 모든 파서 즉시 동작, 선택지 없음
   - 파서 확장은 v2에서 사용자 요청 시 검토

**전략 평가 변화**:
| 항목 | Before | After |
|---|---|---|
| 차별화 | ⭐4 | ⭐5 (Graph RAG 포지셔닝 + 안티타겟) |
| ModolAI 시너지 | ⭐4 | ⭐5 (스키마 브릿지 + 마이그레이션) |
| 실행 가능성 | ⭐4 | ⭐5 (AGPL 지뢰 제거 + 심플 파서) |
| 경쟁력 | ⭐4 | ⭐5 (R2R 빈자리 + 경쟁 분석) |

**참고 소스**:
- RAGFlow: github.com/infiniflow/ragflow (75.2K⭐)
- R2R: github.com/SciPhi-AI/R2R (7.7K⭐, v3.6.5 2025.06 마지막)
- LightRAG: github.com/HKUDS/LightRAG (29.5K⭐, EMNLP 2025)
- pgvector 벤치마크: salttechno.ai (Q1 2026), dev.to (2026.03)
- PyMuPDF 라이선스: AGPL-3.0 (Artifex dual-license)
- docling: MIT (IBM → Linux Foundation)

---

### 2026-03-17 — 전략 문서 초기 작성 (v0.1)

**배경**: ModolAI에 RAG 기능을 추가하기 위해 별도 오픈소스 프로젝트로 ModolRAG 기획. 기존 프레임워크(LangChain, LlamaIndex) 미사용, PostgreSQL(pgvector) 기반 자체 구현.

**결정 사항**:
- DB: PostgreSQL + pgvector (Supabase 호환)
- 검색: 벡터 + FTS + 그래프 → RRF 융합
- 백엔드: FastAPI + 내장 React SPA
- 배포: pip install + Docker Compose
- 인증: X-API-Key
- 테이블 프리픽스: `modolrag_`

**산출물**: `modolrag.md` 전략 문서 v0.1 (22개 태스크, 4 웨이브)
