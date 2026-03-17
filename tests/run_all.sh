#!/bin/bash
set -e
echo "=================================="
echo "  ModolRAG — Test Suite"
echo "=================================="
echo ""

cd "$(dirname "$0")/.."

echo "[1/3] Unit Tests (pytest)..."
python3.11 -m pytest tests/ -v --tb=short
echo ""

echo "[2/3] API Health Check..."
if curl -sf http://localhost:8009/health > /dev/null 2>&1; then
  echo "  ✅ Server is running"
  echo "  Testing endpoints..."
  
  PASS=0; FAIL=0
  for ep in "/health" "/api/documents" "/api/collections" "/api/settings"; do
    CODE=$(curl -so /dev/null -w "%{http_code}" "http://localhost:8009$ep" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
      echo "  ✅ GET $ep → $CODE"
      PASS=$((PASS+1))
    else
      echo "  ❌ GET $ep → $CODE"
      FAIL=$((FAIL+1))
    fi
  done

  # Test search
  CODE=$(curl -so /dev/null -w "%{http_code}" -X POST http://localhost:8009/api/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test","top_k":1}' 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    echo "  ✅ POST /api/search → $CODE"
    PASS=$((PASS+1))
  else
    echo "  ❌ POST /api/search → $CODE"
    FAIL=$((FAIL+1))
  fi

  echo ""
  echo "  API: $PASS passed, $FAIL failed"
else
  echo "  ⚠️  Server not running (skipping API tests)"
  echo "  Start with: ./start.sh"
fi

echo ""
echo "[3/3] Lint Check..."
if command -v ruff > /dev/null 2>&1; then
  ruff check modolrag/ --select E,F --ignore E501 --quiet && echo "  ✅ No lint errors" || echo "  ⚠️  Lint issues found"
else
  echo "  ⏭️  ruff not installed (skipping)"
fi

echo ""
echo "=================================="
echo "  Done!"
echo "=================================="
