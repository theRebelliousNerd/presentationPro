# Presentation Pro - Docker Infrastructure Management
# ================================================

.PHONY: help build build-dev build-prod up up-dev up-prod down down-all logs logs-follow clean prune test health status scale restart

# Default target
help: ## Show this help message
	@echo "Presentation Pro - Docker Infrastructure Management"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment variables
ENV_FILE ?= .env
COMPOSE_PROJECT_NAME ?= presentationpro
DOCKER_BUILDKIT ?= 1
COMPOSE_DOCKER_CLI_BUILD ?= 1

# Export environment variables
export DOCKER_BUILDKIT COMPOSE_DOCKER_CLI_BUILD

# Build commands
build: ## Build all services for development
	@echo "Building all services for development..."
	docker compose build --parallel

build-dev: ## Build all services with development overrides
	@echo "Building all services with development overrides..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel

build-prod: ## Build all services for production
	@echo "Building all services for production..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel --no-cache

build-frontend: ## Build only frontend service
	@echo "Building frontend service..."
	docker compose build web

build-backend: ## Build all backend services (orchestrator, agents, mcp-server)
	@echo "Building backend services..."
	docker compose build orchestrator clarifier outline slide-writer critic notes-polisher design script-writer research mcp-server

# Run commands
up: ## Start all services in development mode
	@echo "Starting all services in development mode..."
	docker compose up -d
	@echo "Services started. Frontend available at http://localhost:3000"
	@echo "ArangoDB available at http://localhost:8530"
	@echo "Use 'make logs' to view logs or 'make health' to check status"

up-dev: ## Start all services with development overrides
	@echo "Starting all services with development overrides..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "Development services started with hot reloading enabled"
	@echo "Additional services: MailHog at http://localhost:8025, Redis at localhost:6379"

up-prod: ## Start all services in production mode
	@echo "Starting all services in production mode..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production services started"
	@echo "Monitoring: Prometheus at http://localhost:9090, Grafana at http://localhost:3001"

up-frontend: ## Start only frontend and required dependencies
	@echo "Starting frontend and dependencies..."
	docker compose up -d web orchestrator arangodb

up-agents: ## Start all agents
	@echo "Starting all agents..."
	docker compose up -d clarifier outline slide-writer critic notes-polisher design script-writer research

# Stop commands
down: ## Stop all services
	@echo "Stopping all services..."
	docker compose down

down-all: ## Stop all services and remove volumes
	@echo "Stopping all services and removing volumes..."
	docker compose down -v --remove-orphans

down-dev: ## Stop development services
	@echo "Stopping development services..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

down-prod: ## Stop production services
	@echo "Stopping production services..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v

# Logs and monitoring
logs: ## Show logs for all services
	docker compose logs --tail=50

logs-follow: ## Follow logs for all services
	docker compose logs -f

logs-web: ## Show logs for frontend service
	docker compose logs -f web

logs-orchestrator: ## Show logs for orchestrator service
	docker compose logs -f orchestrator

logs-agents: ## Show logs for all agents
	docker compose logs -f clarifier outline slide-writer critic notes-polisher design script-writer research

logs-db: ## Show logs for database services
	docker compose logs -f arangodb

# Health and status
health: ## Check health status of all services
	@echo "Checking health status of all services..."
	@docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Service Health Checks:"
	@for service in web orchestrator clarifier outline slide-writer critic notes-polisher design script-writer research mcp-server arangodb; do \
		echo -n "$$service: "; \
		if docker compose exec -T $$service curl -f http://localhost:$$(docker compose port $$service 80 2>/dev/null | cut -d: -f2)/health >/dev/null 2>&1; then \
			echo "✓ Healthy"; \
		else \
			echo "✗ Unhealthy"; \
		fi; \
	done

status: ## Show detailed status of all services
	@echo "=== Service Status ==="
	docker compose ps
	@echo ""
	@echo "=== Resource Usage ==="
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Scaling
scale-agents: ## Scale agent services (usage: make scale-agents REPLICAS=3)
	@echo "Scaling agent services to $(REPLICAS) replicas..."
	docker compose up -d --scale clarifier=$(REPLICAS) --scale outline=$(REPLICAS) --scale slide-writer=$(REPLICAS) --scale critic=$(REPLICAS) --scale notes-polisher=$(REPLICAS) --scale design=$(REPLICAS) --scale script-writer=$(REPLICAS) --scale research=$(REPLICAS)

scale-orchestrator: ## Scale orchestrator service (usage: make scale-orchestrator REPLICAS=2)
	@echo "Scaling orchestrator to $(REPLICAS) replicas..."
	docker compose up -d --scale orchestrator=$(REPLICAS)

# Restart commands
restart: ## Restart all services
	@echo "Restarting all services..."
	docker compose restart

restart-frontend: ## Restart frontend service
	@echo "Restarting frontend service..."
	docker compose restart web

restart-backend: ## Restart backend services
	@echo "Restarting backend services..."
	docker compose restart orchestrator clarifier outline slide-writer critic notes-polisher design script-writer research mcp-server

restart-db: ## Restart database service
	@echo "Restarting database service..."
	docker compose restart arangodb

# Testing
test: ## Run tests in containers
	@echo "Running tests..."
	docker compose exec web npm test
	docker compose exec orchestrator python -m pytest tests/ -v

test-e2e: ## Run end-to-end tests
	@echo "Running end-to-end tests..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web npm run test:e2e

# Database management
db-init: ## Initialize ArangoDB with required databases and collections
	@echo "Initializing ArangoDB..."
	docker compose exec arangodb arangosh --server.password root --javascript.execute-string "db._createDatabase('presentations'); db._useDatabase('presentations'); db._createDocumentCollection('documents'); db._createDocumentCollection('embeddings');"

db-backup: ## Backup ArangoDB data
	@echo "Creating database backup..."
	mkdir -p ./backups
	docker compose exec arangodb arangodump --server.password root --output-directory /tmp/backup
	docker cp $$(docker compose ps -q arangodb):/tmp/backup ./backups/arangodb-$$(date +%Y%m%d_%H%M%S)

db-restore: ## Restore ArangoDB data (usage: make db-restore BACKUP_DIR=./backups/arangodb-20240101_120000)
	@echo "Restoring database from $(BACKUP_DIR)..."
	docker cp $(BACKUP_DIR) $$(docker compose ps -q arangodb):/tmp/restore
	docker compose exec arangodb arangorestore --server.password root --input-directory /tmp/restore

# Development helpers
shell-web: ## Open shell in web container
	docker compose exec web sh

shell-orchestrator: ## Open shell in orchestrator container
	docker compose exec orchestrator bash

shell-agent: ## Open shell in agent container (usage: make shell-agent AGENT=clarifier)
	docker compose exec $(AGENT) bash

shell-db: ## Open ArangoDB shell
	docker compose exec arangodb arangosh --server.password root

# Cleanup
clean: ## Remove all containers, images, and volumes
	@echo "Removing all containers, images, and volumes..."
	docker compose down -v --remove-orphans --rmi all

prune: ## Prune unused Docker resources
	@echo "Pruning unused Docker resources..."
	docker system prune -af --volumes

clean-images: ## Remove all project-related images
	@echo "Removing all project images..."
	docker images | grep $(COMPOSE_PROJECT_NAME) | awk '{print $$3}' | xargs docker rmi -f

clean-volumes: ## Remove all project volumes
	@echo "Removing all project volumes..."
	docker volume ls | grep $(COMPOSE_PROJECT_NAME) | awk '{print $$2}' | xargs docker volume rm -f

# Production deployment
deploy: ## Deploy to production (requires environment setup)
	@echo "Deploying to production..."
	@if [ ! -f .env.production ]; then echo "Error: .env.production file not found"; exit 1; fi
	docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build

deploy-rollback: ## Rollback production deployment
	@echo "Rolling back production deployment..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "Manual intervention required to restore previous state"

# Security
security-scan: ## Run security scan on images
	@echo "Running security scans..."
	@for image in $$(docker compose config --images); do \
		echo "Scanning $$image..."; \
		docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image $$image; \
	done

# Monitoring setup
setup-monitoring: ## Setup monitoring directories and configs
	@echo "Setting up monitoring configuration..."
	mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources},loki}
	mkdir -p nginx/ssl
	mkdir -p secrets
	@echo "Please configure monitoring files in ./monitoring/"

# Quick actions
quick-dev: build-dev up-dev health ## Quick development setup: build, start, and check health
quick-prod: build-prod up-prod health ## Quick production setup: build, start, and check health
quick-test: up-dev test down-dev ## Quick test: start dev environment, run tests, and cleanup

# Variables for common operations
REPLICAS ?= 2
AGENT ?= clarifier
BACKUP_DIR ?= ./backups/latest