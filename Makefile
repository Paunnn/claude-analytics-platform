.PHONY: setup ingest run test clean logs restart db-shell api-shell help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)Claude Analytics Platform - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  $(YELLOW)make setup$(NC)     - Build and start all services (docker-compose up --build)"
	@echo "  $(YELLOW)make ingest$(NC)    - Run ETL pipeline to load data"
	@echo "  $(YELLOW)make run$(NC)       - Start all services (without rebuild)"
	@echo "  $(YELLOW)make test$(NC)      - Run pytest test suite"
	@echo "  $(YELLOW)make clean$(NC)     - Stop services and remove volumes"
	@echo "  $(YELLOW)make logs$(NC)      - Show logs from all services"
	@echo "  $(YELLOW)make restart$(NC)   - Restart all services"
	@echo "  $(YELLOW)make db-shell$(NC)  - Open PostgreSQL shell"
	@echo "  $(YELLOW)make api-shell$(NC) - Open bash shell in API container"
	@echo ""

setup:
	@echo "$(BLUE)Building and starting all services...$(NC)"
	docker-compose up --build -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo ""
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo ""
	@echo "Services running:"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - API:        http://localhost:8000"
	@echo "  - Dashboard:  http://localhost:8501"
	@echo ""
	@echo "Next: run 'make ingest' to load data"

ingest:
	@echo "$(BLUE)Running ETL pipeline...$(NC)"
	docker-compose exec api python scripts/run_etl.py
	@echo "$(GREEN)ETL complete!$(NC)"

run:
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services running:$(NC)"
	@docker-compose ps

test:
	@echo "$(BLUE)Running tests...$(NC)"
	docker-compose exec api pytest tests/ -v --cov=. --cov-report=term-missing

clean:
	@echo "$(YELLOW)Stopping services and removing volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Cleanup complete!$(NC)"

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-dashboard:
	docker-compose logs -f dashboard

logs-db:
	docker-compose logs -f postgres

restart:
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Services restarted!$(NC)"

db-shell:
	docker-compose exec postgres psql -U claude -d claude_analytics

api-shell:
	docker-compose exec api /bin/bash

dashboard-shell:
	docker-compose exec dashboard /bin/bash

# Check service health
health:
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo ""
	@echo "PostgreSQL:"
	@docker-compose exec postgres pg_isready -U claude -d claude_analytics || echo "Not ready"
	@echo ""
	@echo "API Health:"
	@curl -s http://localhost:8000/health/ || echo "Not accessible"
	@echo ""
	@echo "API Ready:"
	@curl -s http://localhost:8000/health/ready || echo "Not ready"

# Quick test endpoints
test-api:
	@echo "$(BLUE)Testing API endpoints...$(NC)"
	@echo ""
	@echo "Root:"
	@curl -s http://localhost:8000/ | jq '.'
	@echo ""
	@echo "Health:"
	@curl -s http://localhost:8000/health/ | jq '.'
	@echo ""
	@echo "Overview:"
	@curl -s http://localhost:8000/analytics/summary/overview | jq '.'

# Development
dev:
	docker-compose up

# Build only
build:
	docker-compose build

# Stop services (without removing volumes)
stop:
	docker-compose stop

# View running containers
ps:
	docker-compose ps

# Show resource usage
stats:
	docker stats --no-stream

# Full workflow
full: setup ingest test-api
	@echo "$(GREEN)Full setup complete!$(NC)"
	@echo "Open http://localhost:8501 to view the dashboard"
