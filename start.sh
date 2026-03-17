#!/bin/bash
set -e

echo "=================================="
echo "  ModolRAG — Starting All Services"
echo "=================================="
echo ""

# 0. Check Docker
echo "[0/4] Checking Docker..."
if docker ps > /dev/null 2>&1; then
    echo "  ✅ Docker is running"
else
    echo "  ⚠️  Docker not running. Starting Docker Desktop..."
    open -a Docker 2>/dev/null || true
    for i in $(seq 1 30); do
        if docker ps > /dev/null 2>&1; then
            echo "  ✅ Docker started"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "  ❌ Docker failed to start. Please open Docker Desktop manually."
            exit 1
        fi
        sleep 2
    done
fi

# 1. Check Ollama
echo ""
echo "[1/4] Checking Ollama..."
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  ✅ Ollama is running at :11434"
else
    echo "  ⚠️  Ollama not running. Starting..."
    if command -v ollama &> /dev/null; then
        ollama serve > /dev/null 2>&1 &
        sleep 3
        if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "  ✅ Ollama started"
        else
            echo "  ❌ Ollama failed to start"
            exit 1
        fi
    else
        echo "  ❌ Ollama not installed. Install: brew install ollama"
        echo "     Or use OpenAI: set MODOLRAG_EMBEDDING_PROVIDER=openai in .env"
        exit 1
    fi
fi

# 2. Check embedding model
echo ""
echo "[2/4] Checking embedding model..."
if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    echo "  ✅ nomic-embed-text is ready"
else
    echo "  ⬇️  Pulling nomic-embed-text (first time only)..."
    ollama pull nomic-embed-text
    echo "  ✅ Model downloaded"
fi

# 3. Start Docker services (PostgreSQL + ModolRAG)
echo ""
echo "[3/4] Starting Docker services..."
cd "$(dirname "$0")"
docker compose up -d --build

# 4. Wait for health check
echo ""
echo "[4/4] Waiting for ModolRAG to be ready..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:8009/health > /dev/null 2>&1; then
        echo "  ✅ ModolRAG is ready!"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "  ❌ Timeout. Checking logs..."
        docker compose logs --tail=20 modolrag
        exit 1
    fi
    printf "."
    sleep 2
done

echo ""
echo "=================================="
echo "  All services running!"
echo "=================================="
echo ""
echo "  📊 Dashboard:    http://localhost:8009/dashboard"
echo "  📖 Swagger UI:   http://localhost:8009/docs"
echo "  📋 ReDoc:        http://localhost:8009/redoc"
echo "  🔍 Health:       http://localhost:8009/health"
echo "  🐘 PostgreSQL:   localhost:5439"
echo "  🦙 Ollama:       localhost:11434"
echo ""
echo "  Stop:   cd $(pwd) && docker compose down"
echo "  Logs:   cd $(pwd) && docker compose logs -f modolrag"
echo ""
