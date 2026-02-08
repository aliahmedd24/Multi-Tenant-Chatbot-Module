#!/bin/bash

set -e

echo "Running database migrations..."

# Check if a migration message was provided
if [ -n "$1" ]; then
    echo "Generating new migration: $1"
    docker compose run --rm backend alembic revision --autogenerate -m "$1"
fi

echo "Applying migrations..."
docker compose run --rm backend alembic upgrade head

echo "Current migration status:"
docker compose run --rm backend alembic current

echo "Migrations complete!"
