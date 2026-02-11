#!/bin/bash

echo "🔍 Finding what's using port 5000..."
lsof -i :5000

echo ""
echo "On macOS, this is often AirPlay Receiver."
echo ""
echo "To fix:"
echo "1. System Preferences → Sharing → Uncheck 'AirPlay Receiver'"
echo "   OR"
echo "2. Kill the process using port 5000"
echo ""
echo "Then run: docker compose up"
