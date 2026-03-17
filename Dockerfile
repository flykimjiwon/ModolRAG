# Stage 1: Build dashboard
FROM node:20-slim AS dashboard-builder
WORKDIR /dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY dashboard/ .
RUN npm run build
# Output: /dashboard/../modolrag/static/ → /modolrag/static/

# Stage 2: Python application
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY pyproject.toml setup.py ./
COPY modolrag/__init__.py modolrag/__init__.py
RUN pip install --no-cache-dir .

# Copy application code
COPY modolrag/ modolrag/
COPY modolrag.md ./

# Copy built dashboard from Stage 1
COPY --from=dashboard-builder /modolrag/static/ modolrag/static/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "modolrag.main:app", "--host", "0.0.0.0", "--port", "8000"]
