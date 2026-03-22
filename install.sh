#!/bin/bash
# ══════════════════════════════════════════════════════════
#  ModolRAG 원클릭 설치 스크립트
#  코드를 몰라도 이 스크립트 하나면 전부 설치됩니다.
#
#  사용법: curl -sSL https://raw.githubusercontent.com/modolai/ModolRAG/main/install.sh | bash
#  또는:   bash install.sh
# ══════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "══════════════════════════════════════════════"
echo "       ModolRAG 원클릭 설치"
echo "       코드 몰라도 OK. 따라만 하세요."
echo "══════════════════════════════════════════════"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi
echo -e "${BLUE}[INFO]${NC} 운영체제: $OS"
echo ""

# ─── 1. Python ───────────────────────────────────────────
echo -e "${BLUE}[1/5]${NC} Python 확인 중..."
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✅${NC} $PY_VER"
else
    echo -e "  ${RED}❌${NC} Python이 설치되어 있지 않습니다."
    if [ "$OS" = "macos" ]; then
        echo "     설치 방법: brew install python@3.11"
    elif [ "$OS" = "linux" ]; then
        echo "     설치 방법: sudo apt install python3 python3-pip"
    fi
    echo "     Python 설치 후 이 스크립트를 다시 실행해주세요."
    exit 1
fi

# ─── 2. Docker ───────────────────────────────────────────
echo ""
echo -e "${BLUE}[2/5]${NC} Docker 확인 중..."
if command -v docker &>/dev/null; then
    if docker ps &>/dev/null; then
        echo -e "  ${GREEN}✅${NC} Docker 실행 중"
    else
        echo -e "  ${YELLOW}⚠️${NC}  Docker가 설치되어 있지만 실행되지 않고 있습니다."
        if [ "$OS" = "macos" ]; then
            echo "     Docker Desktop을 실행해주세요. (Spotlight에서 'Docker' 검색)"
            open -a Docker 2>/dev/null || true
            echo "     Docker가 시작되면 이 스크립트를 다시 실행해주세요."
        else
            echo "     실행 방법: sudo systemctl start docker"
        fi
        exit 1
    fi
else
    echo -e "  ${RED}❌${NC} Docker가 설치되어 있지 않습니다."
    if [ "$OS" = "macos" ]; then
        echo "     설치 방법: brew install --cask docker"
        echo "     또는: https://www.docker.com/products/docker-desktop"
    elif [ "$OS" = "linux" ]; then
        echo "     설치 방법: https://docs.docker.com/engine/install/"
    fi
    echo "     Docker 설치 후 이 스크립트를 다시 실행해주세요."
    exit 1
fi

# ─── 3. Ollama ───────────────────────────────────────────
echo ""
echo -e "${BLUE}[3/5]${NC} Ollama 확인 중..."
if command -v ollama &>/dev/null; then
    echo -e "  ${GREEN}✅${NC} Ollama 설치됨"

    # Check if running
    if curl -sf http://localhost:11434/api/tags &>/dev/null; then
        echo -e "  ${GREEN}✅${NC} Ollama 실행 중"
    else
        echo -e "  ${YELLOW}⚠️${NC}  Ollama 시작 중..."
        ollama serve &>/dev/null &
        sleep 3
        if curl -sf http://localhost:11434/api/tags &>/dev/null; then
            echo -e "  ${GREEN}✅${NC} Ollama 시작됨"
        fi
    fi

    # Pull embedding model
    if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
        echo -e "  ${GREEN}✅${NC} 임베딩 모델 (nomic-embed-text) 준비됨"
    else
        echo -e "  ${YELLOW}⬇️${NC}  임베딩 모델 다운로드 중... (약 274MB, 1~3분 소요)"
        ollama pull nomic-embed-text
        echo -e "  ${GREEN}✅${NC} 임베딩 모델 준비됨"
    fi
else
    echo -e "  ${YELLOW}⚠️${NC}  Ollama가 설치되어 있지 않습니다. (선택사항)"
    if [ "$OS" = "macos" ]; then
        echo "     설치하시겠습니까? (AI 문서 검색에 필요)"
        read -p "     [Y/n]: " install_ollama
        if [ "$install_ollama" != "n" ] && [ "$install_ollama" != "N" ]; then
            echo "     Ollama 설치 중..."
            brew install ollama 2>/dev/null || {
                echo "     brew가 없습니다. https://ollama.ai 에서 직접 설치해주세요."
            }
            ollama serve &>/dev/null &
            sleep 3
            ollama pull nomic-embed-text
        fi
    else
        echo "     설치: https://ollama.ai"
    fi
fi

# ─── 4. ModolRAG 설치 ────────────────────────────────────
echo ""
echo -e "${BLUE}[4/5]${NC} ModolRAG 설치 중..."

# Check if already in ModolRAG directory
if [ -f "pyproject.toml" ] && grep -q "modolrag" pyproject.toml 2>/dev/null; then
    echo "  ModolRAG 프로젝트 폴더에서 실행 중..."
    pip3 install -e ".[dev]" --quiet 2>/dev/null || pip install -e ".[dev]" --quiet 2>/dev/null
else
    # Install from current directory or clone
    if [ -d "ModolRAG" ]; then
        cd ModolRAG
    elif [ -f "../pyproject.toml" ] && grep -q "modolrag" ../pyproject.toml 2>/dev/null; then
        cd ..
    fi
    pip3 install -e ".[dev]" --quiet 2>/dev/null || pip install -e ".[dev]" --quiet 2>/dev/null
fi

echo -e "  ${GREEN}✅${NC} ModolRAG 설치됨"

# ─── 5. 서비스 시작 ──────────────────────────────────────
echo ""
echo -e "${BLUE}[5/5]${NC} 서비스 시작 중..."

# Start PostgreSQL via docker compose
if [ -f "docker-compose.yml" ]; then
    docker compose up -d db 2>/dev/null
    echo "  PostgreSQL 시작 대기 중..."
    for i in $(seq 1 15); do
        if docker compose exec -T db pg_isready -U modolrag &>/dev/null; then
            break
        fi
        sleep 2
    done
    echo -e "  ${GREEN}✅${NC} PostgreSQL 준비됨"
else
    echo -e "  ${YELLOW}⚠️${NC}  docker-compose.yml을 찾을 수 없습니다."
    echo "     수동 실행: docker run -d --name modolrag-db -e POSTGRES_DB=modolrag -e POSTGRES_USER=modolrag -e POSTGRES_PASSWORD=modolrag -p 5432:5432 pgvector/pgvector:pg15"
fi

# Initialize DB
echo "  데이터베이스 초기화 중..."
python3 -c "
import asyncio
from modolrag.db import init_schema, close_pool
async def init():
    await init_schema()
    await close_pool()
    print('  ✅ 데이터베이스 준비됨')
asyncio.run(init())
" 2>/dev/null || echo -e "  ${YELLOW}⚠️${NC}  DB 초기화 실패. MODOLRAG_POSTGRES_URI를 확인해주세요."

# Start server
echo ""
echo "══════════════════════════════════════════════"
echo -e "  ${GREEN}설치 완료!${NC}"
echo "══════════════════════════════════════════════"
echo ""
echo "  서버 시작:     modolrag serve"
echo "  대시보드 열기: http://localhost:8000/dashboard"
echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │  대시보드에서 할 수 있는 것:             │"
echo "  │                                          │"
echo "  │  📄 Documents → 파일 업로드              │"
echo "  │  🔍 Search    → 검색하기                 │"
echo "  │  🕸️  Graph     → 관계도 보기              │"
echo "  │  📁 Collections → 문서 분류              │"
echo "  │  🤖 Apps      → AI 챗봇 만들기           │"
echo "  │  ⚙️  Settings  → 설정 변경               │"
echo "  └──────────────────────────────────────────┘"
echo ""
echo "  지금 바로 시작하시겠습니까?"
read -p "  [Y/n]: " start_now
if [ "$start_now" != "n" ] && [ "$start_now" != "N" ]; then
    echo ""
    echo "  서버를 시작합니다... (Ctrl+C로 종료)"
    echo "  대시보드: http://localhost:8000/dashboard"
    echo ""
    modolrag serve --port 8000
fi
