#!/bin/sh
echo "Running database seed..."
python seed_users.py
echo "Starting server..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app
