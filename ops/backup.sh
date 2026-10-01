#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/risheh-engage-$TIMESTAMP.dump"

echo "Creating PostgreSQL backup: $FILE"
pg_dump --format=custom --no-owner --no-acl --dbname="$DATABASE_URL" --file="$FILE"

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$FILE" > "$FILE.sha256"
fi

find "$BACKUP_DIR" -type f -name 'risheh-engage-*.dump*' -mtime "+$RETENTION_DAYS" -delete || true

echo "Backup complete: $FILE"
