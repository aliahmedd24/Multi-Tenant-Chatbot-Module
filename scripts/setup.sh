#!/bin/bash

set -e  # Exit on error

echo "Wafaa Platform Setup"
echo "======================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker not found. Please install Docker."; exit 1; }
command -v docker compose >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose not found."; exit 1; }

echo "Prerequisites check passed"

# Create environment files
echo "Creating environment files..."

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env (please update with your settings)"
fi

if [ ! -f dashboard/.env ]; then
    cp dashboard/.env.example dashboard/.env
    echo "Created dashboard/.env"
fi

# Install pre-commit hooks (if pre-commit is available)
if command -v pre-commit >/dev/null 2>&1; then
    echo "Installing pre-commit hooks..."
    pre-commit install
    echo "Pre-commit hooks installed"
else
    echo "pre-commit not found - skipping hook installation"
    echo "Install with: pip install pre-commit"
fi

# Start services
echo "Starting Docker services..."
docker compose up -d postgres redis

# Wait for database
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
docker compose run --rm backend alembic upgrade head

# Seed data
echo "Seeding initial data..."
docker compose run --rm backend python scripts/seed_data.py

# Start all services
echo "Starting all services..."
docker compose up -d

echo ""
echo "Setup complete!"
echo ""
echo "Services available at:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Dashboard: http://localhost:5173"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop services: docker compose down"
