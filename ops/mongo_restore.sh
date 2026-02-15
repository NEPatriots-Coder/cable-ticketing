#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/ticketing.archive.gz"
  exit 1
fi

ARCHIVE_PATH="$1"

if [ ! -f "${ARCHIVE_PATH}" ]; then
  echo "Archive not found: ${ARCHIVE_PATH}"
  exit 1
fi

gunzip -c "${ARCHIVE_PATH}" | docker exec -i cable-ticketing-mongo mongorestore --archive --drop
echo "Restore complete from ${ARCHIVE_PATH}"
