# Makefile for PurrFect Spots Project
# This file provides convenient targets for building the project

.PHONY: help build build-frontend build-backend clean clean-frontend clean-backend install install-frontend install-backend test test-frontend test-backend lint lint-frontend lint-backend deploy deploy-staging deploy-production

# Default target
help:
	@echo "PurrFect Spots Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  help                 - Show this help message"
	@echo "  build                - Build the entire project for production"
	@echo "  build-dev            - Build the entire project for development"
	@echo "  build-staging        - Build the entire project for staging"
	@echo "  build-frontend       - Build only the frontend for production"
	@echo "  build-frontend-dev   - Build only the frontend for development"
	@echo "  build-frontend-staging - Build only the frontend for staging"
	@echo "  build-backend        - Build only the backend for production"
	@echo "  build-backend-dev    - Build only the backend for development"
	@echo "  build-backend-staging - Build only the backend for staging"
	@echo "  clean                - Clean all build artifacts"
	@echo "  clean-frontend       - Clean frontend build artifacts"
	@echo "  clean-backend        - Clean backend build artifacts"
	@echo "  install              - Install all dependencies"
	@echo "  install-frontend     - Install frontend dependencies"
	@echo "  install-backend      - Install backend dependencies"
	@echo "  test                 - Run all tests"
	@echo "  test-frontend        - Run frontend tests"
	@echo "  test-backend         - Run backend tests"
	@echo "  lint                 - Run all linting"
	@echo "  lint-frontend        - Run frontend linting"
	@echo "  lint-backend         - Run backend linting"
	@echo "  deploy-staging       - Deploy to staging environment"
	@echo "  deploy-production    - Deploy to production environment"

# Build targets
build:
	@echo "Building the entire project for production..."
	./build.sh production

build-dev:
	@echo "Building the entire project for development..."
	./build.sh development

build-staging:
	@echo "Building the entire project for staging..."
	./build.sh staging

build-frontend:
	@echo "Building frontend for production..."
	./build.sh production frontend-only

build-frontend-dev:
	@echo "Building frontend for development..."
	./build.sh development frontend-only

build-frontend-staging:
	@echo "Building frontend for staging..."
	./build.sh staging frontend-only

build-backend:
	@echo "Building backend for production..."
	./build.sh production backend-only

build-backend-dev:
	@echo "Building backend for development..."
	./build.sh development backend-only

build-backend-staging:
	@echo "Building backend for staging..."
	./build.sh staging backend-only

# Clean targets
clean:
	@echo "Cleaning all build artifacts..."
	rm -rf frontend/dist
	rm -rf backend/venv
	rm -rf build-reports
	rm -f frontend/build-report-*.json
	rm -f backend/build-report-*.json

clean-frontend:
	@echo "Cleaning frontend build artifacts..."
	rm -rf frontend/dist
	rm -f frontend/build-report-*.json

clean-backend:
	@echo "Cleaning backend build artifacts..."
	rm -rf backend/venv
	rm -f backend/build-report-*.json

# Install targets
install:
	@echo "Installing all dependencies..."
	$(MAKE) install-frontend
	$(MAKE) install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Test targets
test:
	@echo "Running all tests..."
	$(MAKE) test-frontend
	$(MAKE) test-backend

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend:
	@echo "Running backend tests..."
	cd backend && source venv/bin/activate && python -m pytest

# Lint targets
lint:
	@echo "Running all linting..."
	$(MAKE) lint-frontend
	$(MAKE) lint-backend

lint-frontend:
	@echo "Running frontend linting..."
	cd frontend && npm run lint

lint-backend:
	@echo "Running backend linting..."
	cd backend && source venv/bin/activate && flake8 .

# Deploy targets
deploy-staging:
	@echo "Deploying to staging environment..."
	./build.sh staging
	# Add deployment commands here

deploy-production:
	@echo "Deploying to production environment..."
	./build.sh production
	# Add deployment commands here

# Development targets
dev:
	@echo "Starting development servers..."
	@echo "Starting frontend server..."
	cd frontend && npm run dev &
	@echo "Starting backend server..."
	cd backend && source venv/bin/activate && python main.py &
	@echo "Development servers started. Press Ctrl+C to stop."

dev-frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

dev-backend:
	@echo "Starting backend development server..."
	cd backend && source venv/bin/activate && python main.py