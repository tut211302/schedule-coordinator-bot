#!/bin/bash

# LINE Bot Models Setup Script
# LINEチャネル設定とリッチメニュー定義のセットアップ

echo "============================================================"
echo "LINE Bot チャネル設定・リッチメニュー定義セットアップ"
echo "============================================================"
echo ""

# Step 1: Check if running in Docker container
if [ ! -f "/.dockerenv" ]; then
    echo "⚠️  このスクリプトはDockerコンテナ内で実行してください"
    echo "   docker exec -it schedule-coordinator-backend bash"
    echo "   cd /app && bash setup_line_models.sh"
    exit 1
fi

# Step 2: Check database connection
echo "📡 データベース接続を確認中..."
python3 -c "from database import check_db_connection; import sys; sys.exit(0 if check_db_connection() else 1)"
if [ $? -eq 0 ]; then
    echo "✅ データベース接続成功"
else
    echo "❌ データベース接続失敗"
    echo "   データベースコンテナが起動しているか確認してください"
    exit 1
fi

# Step 3: Install dependencies
echo ""
echo "📦 依存関係をインストール中..."
poetry install --no-root
if [ $? -eq 0 ]; then
    echo "✅ 依存関係インストール完了"
else
    echo "❌ 依存関係インストール失敗"
    exit 1
fi

# Step 4: Run model tests
echo ""
echo "🧪 モデルテストを実行中..."
python3 test_models.py
TEST_RESULT=$?

# Summary
echo ""
echo "============================================================"
echo "セットアップ完了"
echo "============================================================"

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ すべてのテストが成功しました！"
    echo ""
    echo "次のステップ:"
    echo "1. backend/LINE_BOT_MODELS_GUIDE.md でドキュメントを確認"
    echo "2. FastAPIエンドポイントを実装"
    echo "3. LINE Messaging APIと統合"
    echo ""
    echo "使用方法:"
    echo "  from models.line_channel import LineChannel"
    echo "  from models.rich_menu import RichMenu"
    echo "  from models.user_rich_menu import UserRichMenu"
    echo "  from database import get_db"
else
    echo "⚠️  一部のテストが失敗しました"
    echo "   詳細はtest_models.pyの出力を確認してください"
    exit 1
fi
