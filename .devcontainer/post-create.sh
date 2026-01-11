#!/bin/bash

set -e

echo "=================================================="
echo "Starting Development Environment Setup"
echo "=================================================="

# フロントエンドの依存関係をインストール
echo ""
echo "📦 Installing frontend dependencies..."
cd /workspace
npm install

# バックエンド用ディレクトリの準備
echo ""
echo "📦 Preparing backend directory..."
if [ ! -f /workspace/backend/pyproject.toml ]; then
    echo "⚠️  Backend pyproject.toml not found. Creating placeholder..."
    cd /workspace/backend
    cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "google-calendar-backend"
version = "0.1.0"
description = "FastAPI backend for Google Calendar integration"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = "^0.24.0"
sqlalchemy = "^2.0"
mysql-connector-python = "^8.2.0"
python-dotenv = "^1.0.0"
google-auth = "^2.25.2"
google-auth-httplib2 = "^0.2.0"
google-auth-oauthlib = "^1.1.0"
pydantic = "^2.4.2"
pydantic-settings = "^2.0.3"

[tool.poetry.dev-dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
black = "^23.11.0"
pylint = "^3.0.2"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
fi

# Poetryのインストール確認
if ! command -v poetry &> /dev/null; then
    echo "📥 Installing Poetry..."
    pip install poetry --quiet
fi

# バックエンドの依存関係をインストール
echo ""
echo "📦 Installing backend dependencies..."
cd /workspace/backend
poetry install

# データベース接続待機
echo ""
echo "⏳ Waiting for database to be ready..."
TIMEOUT=60
ELAPSED=0
DB_HOST="db"
DB_PORT=3306
DB_USER="devuser"
DB_PASSWORD="devpass123"

while ! mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "❌ Database failed to start within $TIMEOUT seconds"
        exit 1
    fi
    echo "⏳ Waiting for MySQL... ($ELAPSED/$TIMEOUT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo "✅ Database is ready!"

# .envファイルの作成（開発用）
if [ ! -f /workspace/.env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cat > /workspace/.env << 'EOF'
# Frontend Environment Variables
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id-here.apps.googleusercontent.com
REACT_APP_BACKEND_URL=http://localhost:8000

# Backend Environment Variables (if needed)
BACKEND_ENVIRONMENT=development
DATABASE_URL=mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db
DB_HOST=db
DB_PORT=3306
DB_USER=devuser
DB_PASSWORD=devpass123
DB_NAME=calendar_db
SECRET_KEY=your-super-secret-dev-key-here
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
EOF
    echo "✅ .env file created (please update with your credentials)"
fi

# Node moduleのキャッシュをクリア（オプション）
echo ""
echo "🧹 Cleaning up..."

echo ""
echo "=================================================="
echo "✅ Development environment setup complete!"
echo "=================================================="
echo ""
echo "📚 Available services:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend:  http://localhost:8000"
echo "   • Database: localhost:3306"
echo ""
echo "🚀 To start the development servers:"
echo "   • Frontend: npm start (in /workspace)"
echo "   • Backend:  cd backend && poetry run uvicorn main:app --reload"
echo ""
echo "📖 For more information, see README.md"
echo "=================================================="
