# ModolRAG Frontend Architecture Decision

> **Status**: Analysis complete, ready for implementation
> **Date**: 2026-03-17
> **Decision**: React SPA (Vite) + shadcn/ui 유지 — Next.js 불필요

---

## TL;DR

**Next.js는 필요 없다.** 현재 Vite + React SPA를 유지하고 **shadcn/ui만 추가**하면 된다.

이유:
1. RAG 앱빌더 6개 중 5개가 React SPA 사용 (Next.js는 Dify 1개뿐, 별도 컨테이너 필요)
2. FastAPI가 static 파일 서빙하는 현재 구조가 업계 표준 (Langflow, RAGFlow 동일 패턴)
3. shadcn/ui는 Vite + React에서 완벽 동작 (Next.js 필요 없음)
4. Next.js 도입 시 Node.js 서버 추가 필요 → 배포 복잡도 증가, 자원 낭비

---

## 1. 현재 ModolRAG 아키텍처

```
BUILD: npm run build (tsc -b && vite build)
dashboard/ → modolrag/static/ (HTML+JS+CSS)

RUNTIME: uvicorn modolrag.main:app
FastAPI serves:
  /api/*        → API endpoints
  /dashboard/*  → StaticFiles(html=True) → SPA

DOCKER: Single container
Stage 1: Node.js → npm run build
Stage 2: Python → COPY static/ + run uvicorn
+ PostgreSQL (pgvector) as separate container
```

- **Framework**: React 19 + Vite 8 + Tailwind v4
- **Routing**: react-router-dom (client-side)
- **SSR**: 없음 (100% client-side)
- **Serving**: FastAPI StaticFiles(html=True) — SPA fallback 지원
- **Deployment**: Docker multi-stage build → 단일 컨테이너

---

## 2. 경쟁 RAG 앱빌더 프론트엔드 스택 비교

| 제품 | Stars | Frontend | 렌더링 | Backend | 배포 모델 |
|------|-------|----------|--------|---------|----------|
| **Dify** | 133K | Next.js (React) | SSR | Python/Flask | 별도 컨테이너 (8개 서비스) |
| **Open WebUI** | 128K | SvelteKit | SPA | Python | 단일 컨테이너 |
| **RAGFlow** | 75K | React | SPA | Python | 단일 컨테이너 |
| **AnythingLLM** | 56K | React | SPA | Node.js | 단일 컨테이너 |
| **Flowise** | 50K | React | SPA | Node.js | 단일 컨테이너 |
| **Langflow** | 28K | React + TS | SPA | Python/FastAPI | 단일 컨테이너 |

핵심: 6개 중 5개가 React SPA + 단일 컨테이너. Langflow가 ModolRAG와 가장 유사 (React SPA + FastAPI).

---

## 3. React SPA vs Next.js (ModolRAG 기준)

| 관점 | React SPA (Vite) | Next.js |
|------|-------------------|---------|
| SSR | 없음 (대시보드에 불필요) | 있음 (불필요한 기능) |
| 배포 | FastAPI 단일 컨테이너 | Node.js 서버 추가 필요 |
| 자원 | Python 1개 | Python + Node.js 2개 |
| 빌드 속도 | Vite (즉시) | Next.js (느림) |
| shadcn/ui | 지원 (공식 Vite 가이드) | 기본 지원 |
| 복잡도 | 낮음 | 높음 (RSC, App Router 등) |
| 마이그레이션 비용 | 없음 | 전체 재작성 (1-2주) |

Next.js 도입 시 얻는 것: SSR (불필요), API Routes (FastAPI와 중복)
Next.js 도입 시 잃는 것: 단일 컨테이너, 빠른 빌드, 아키텍처 단순성

---

## 4. 추천 액션 플랜: shadcn/ui 도입

### 설치 순서

```bash
cd dashboard

# 1. tsconfig.app.json path alias 추가
# { "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["./src/*"] } } }

# 2. vite.config.ts alias 추가
# resolve: { alias: { "@": path.resolve(__dirname, "./src") } }

# 3. shadcn/ui 초기화
npx shadcn@latest init

# 4. 핵심 컴포넌트 추가
npx shadcn@latest add button card input textarea select badge
npx shadcn@latest add dialog dropdown-menu separator tabs tooltip
npx shadcn@latest add scroll-area sheet sidebar navigation-menu
```

### 교체 대상

| 현재 (직접 Tailwind) | shadcn/ui |
|---------------------|-----------|
| 직접 Button 스타일 | `<Button variant="default">` |
| 직접 Input 스타일 | `<Input>` |
| 직접 Card 레이아웃 | `<Card><CardHeader><CardContent>` |
| 직접 Badge | `<Badge variant="secondary">` |
| confirm() | `<AlertDialog>` |
| select | `<Select>` |
| range | `<Slider>` |
| Tab 그룹 | `<Tabs><TabsList><TabsTrigger>` |

---

## 5. 앱 빌더 수준 UI를 위한 추가 라이브러리

| 용도 | 라이브러리 | 설명 |
|------|----------|------|
| 플로우 에디터 | `@xyflow/react` | 노드 기반 파이프라인 (Flowise/Langflow 사용) |
| 코드 에디터 | `@monaco-editor/react` | 시스템 프롬프트 편집 |
| 마크다운 | `react-markdown` + `remark-gfm` | RAG 답변 렌더링 |
| 토스트 | `sonner` | 성공/에러 알림 (shadcn 호환) |
| 테이블 | `@tanstack/react-table` | 문서/앱 목록 |
| 채팅 스트리밍 | 직접 구현 (EventSource) | SSE 기반 |

---

## 6. 내일 작업 순서

1. shadcn/ui 초기화 + path alias 설정
2. 기본 컴포넌트 설치 (button, card, input, badge, tabs, dialog 등)
3. Layout.tsx → shadcn Sidebar 컴포넌트 교체
4. 각 페이지 순차 마이그레이션
5. 앱 빌더 페이지 고도화 (React Flow 파이프라인 시각화 등)
6. 채팅 UI에 마크다운 렌더링 + SSE 스트리밍 적용
7. 빌드 검증 + 커밋

---

## 최종 결론

```
❌ Next.js → 배포 복잡도 증가, SSR 불필요, 자원 낭비
✅ React SPA (Vite) + shadcn/ui → 업계 표준, 단순, UI 극적 향상
```
