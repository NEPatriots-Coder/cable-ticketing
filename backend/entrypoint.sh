#!/bin/sh
set -e

if [ "${RUN_SEED_ON_START:-false}" = "true" ]; then
  echo "Running database seed..."
  python seed_users.py
fi

echo "Starting server..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app
