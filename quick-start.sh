#!/bin/bash

# Cable Ticketing System - Quick Start Script
# This script helps you get started quickly

set -e

echo "🔌 Cable Ticketing System - Quick Start"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file from template..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your:"
    echo "   - Twilio credentials (for SMS)"
    echo "   - SendGrid API key (for Email)"
    echo ""
    echo "Press Enter to continue (or Ctrl+C to exit and configure .env first)..."
    read -r
else
    echo "✅ backend/.env already exists"
fi

echo ""
echo "🏗️  Building Docker images (this may take a few minutes)..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
    echo ""
    echo "📱 Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:5000"
    echo ""
    echo "👤 Next steps:"
    echo "   1. Open http://localhost:3000 in your browser"
    echo "   2. Click 'Register' to create your first user"
    echo "   3. Create a ticket and see the magic! ✨"
    echo ""
    echo "📋 Useful commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop services: docker-compose down"
    echo "   - Restart services: docker-compose restart"
    echo ""
    echo "📖 For more info, see README.md"
    echo ""
else
    echo ""
    echo "❌ Services failed to start. Check logs with:"
    echo "   docker-compose logs"
    exit 1
fi
