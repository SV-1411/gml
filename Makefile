.PHONY: help install dev test lint format clean docker-up docker-down

help:
	@echo "GML Infrastructure - Make Commands"
	@echo ""
	@echo "install       Install production dependencies"
	@echo "dev           Install development dependencies"
	@echo "test          Run tests with coverage"
	@echo "lint          Run linting tools"
	@echo "format        Format code with black and isort"
	@echo "clean         Clean up cache and build files"
	@echo "docker-up     Start development environment"
	@echo "docker-down   Stop development environment"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest --cov=src/gml --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

lint:
	flake8 src/ tests/
	pylint src/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/

docker-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose -f docker-compose.dev.yml down

docker-logs:
	docker-compose -f docker-compose.dev.yml logs -f

docker-rebuild:
	docker-compose -f docker-compose.dev.yml up -d --build
