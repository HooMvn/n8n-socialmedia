#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Usage: DATABASE_URL=... ./ops/restore.sh /path/to/backup.dump" >&2
  exit 2
fi

if [ "${ALLOW_DESTRUCTIVE_RESTORE:-no}" != "yes" ]; then
  echo "Refusing restore. Set ALLOW_DESTRUCTIVE_RESTORE=yes after verifying the target database." >&2
  exit 3
fi

echo "Restoring $BACKUP_FILE into configured database"
pg_restore --clean --if-exists --no-owner --no-acl --dbname="$DATABASE_URL" "$BACKUP_FILE"
echo "Restore complete. Run migrations and production smoke next."
