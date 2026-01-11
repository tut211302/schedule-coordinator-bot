#!/bin/bash

# Development environment quick start script
# このスクリプトは開発環境をセットアップして起動します

set -e

echo "🚀 Schedule Coordinator Bot - Dev Setup"
echo "=========================================="
echo ""

# Docker がインストールされているか確認
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Docker Compose がインストールされているか確認
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# コンテナをビルドして起動
echo "🔨 Building and starting containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# 各サービスのヘルスチェック
echo ""
echo "🏥 Health checks:"

# Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend is ready (http://localhost:3000)"
else
    echo "   ⏳ Frontend is starting..."
fi

# Backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Backend is ready (http://localhost:8000)"
else
    echo "   ⏳ Backend is starting..."
fi

# Database
if docker exec calendar-db mysqladmin ping -h localhost -udevuser -pdevpass123 > /dev/null 2>&1; then
    echo "   ✅ Database is ready (localhost:3306)"
else
    echo "   ❌ Database connection failed"
fi

echo ""
echo "=========================================="
echo "✅ Development environment is running!"
echo "=========================================="
echo ""
echo "📍 Access URLs:"
echo "   • Frontend:    http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
echo "   • PHPMyAdmin:  http://localhost:8080"
echo ""
echo "📚 Useful commands:"
echo "   • View logs:           docker-compose logs -f [service]"
echo "   • Stop containers:     docker-compose down"
echo "   • Rebuild containers:  docker-compose up -d --build"
echo "   • Enter frontend:      docker-compose exec frontend bash"
echo "   • Enter backend:       docker-compose exec backend bash"
echo ""
echo "🛑 To stop the development environment:"
echo "   docker-compose down"
echo ""
