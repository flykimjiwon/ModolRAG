FROM python:3.11-slim

WORKDIR /app

# System dependencies for document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml setup.py ./
COPY modolrag/__init__.py modolrag/__init__.py
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Run
CMD ["uvicorn", "modolrag.main:app", "--host", "0.0.0.0", "--port", "8000"]
