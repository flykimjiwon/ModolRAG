.PHONY: dev build test lint docker-up docker-down clean

dev:
	modolrag serve --reload

build:
	pip install -e .

test:
	pytest tests/ -v

lint:
	ruff check modolrag/ tests/
	ruff format --check modolrag/ tests/

format:
	ruff format modolrag/ tests/

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
