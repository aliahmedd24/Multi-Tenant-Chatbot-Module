#!/bin/bash

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/wafaa_db_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo "Backing up database..."
docker compose exec postgres pg_dump -U wafaa_user wafaa_db > "$BACKUP_FILE"

echo "Backup saved to: $BACKUP_FILE"
echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
