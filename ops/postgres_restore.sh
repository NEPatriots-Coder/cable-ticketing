#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/ticketing.dump"
  exit 1
fi

BACKUP_PATH="$1"

if [ ! -f "${BACKUP_PATH}" ]; then
  echo "Backup not found: ${BACKUP_PATH}"
  exit 1
fi

docker exec -i cable-ticketing-postgres dropdb -U ticketing --if-exists ticketing
docker exec -i cable-ticketing-postgres createdb -U ticketing ticketing
cat "${BACKUP_PATH}" | docker exec -i cable-ticketing-postgres pg_restore -U ticketing -d ticketing --clean --if-exists
echo "Restore complete from ${BACKUP_PATH}"
