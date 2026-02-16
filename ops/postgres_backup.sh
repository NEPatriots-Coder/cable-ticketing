#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/cable-ticketing}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_DIR="${BACKUP_DIR}/${STAMP}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "${TARGET_DIR}"

docker exec cable-ticketing-postgres pg_dump -U ticketing -d ticketing -Fc > "${TARGET_DIR}/ticketing.dump"

find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d -mtime +"${RETENTION_DAYS}" -exec rm -rf {} +

echo "Backup complete: ${TARGET_DIR}/ticketing.dump"
