.PHONY: help install test lint format run docker-build docker-up docker-down deploy clean

# Default target
help:
	@echo "Golf Course Delivery System - Available Commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make run          - Run application locally"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start services with Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose services"
	@echo "  make deploy       - Deploy to Kubernetes"
	@echo "  make clean        - Clean up generated files"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src/ --max-line-length=120
	mypy src/ --ignore-missing-imports
	black src/ --check

# Format code
format:
	black src/
	isort src/

# Run application locally
run:
	uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Docker commands
docker-build:
	docker build -t golf-delivery-api:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Kubernetes deployment
deploy: docker-build
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/ingress.yaml

# Database migrations
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(message)"

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache

# Development database
db-setup:
	docker run -d --name golf-postgres \
		-e POSTGRES_USER=golf_user \
		-e POSTGRES_PASSWORD=golf_pass \
		-e POSTGRES_DB=golf_delivery \
		-p 5432:5432 \
		postgres:15

db-stop:
	docker stop golf-postgres
	docker rm golf-postgres

# Redis setup
redis-setup:
	docker run -d --name golf-redis \
		-p 6379:6379 \
		redis:7-alpine

redis-stop:
	docker stop golf-redis
	docker rm golf-redis