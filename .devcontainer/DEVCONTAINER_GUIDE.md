# Dev Container Development Guide

## Overview

Dev Containerは、VS Code Remote - Containers拡張機能を使用して、一貫性のある開発環境をDockerコンテナ内に構築する設定です。これにより、チームメンバー全員が同じツール、依存関係、設定で開発でき、環境による問題を解消します。

## セットアップ

### 前提条件

- **Docker Desktop** がインストールされていること
- **VS Code** がインストールされていること
- **Remote - Containers** 拡張機能がインストールされていること

### 拡張機能のインストール

VS Code の拡張機能マーケットプレイスから「Remote - Containers」をインストール:

```
ms-vscode-remote.remote-containers
```

### Dev Container の起動

1. VS Code でプロジェクトフォルダを開く
2. Command Palette を開く (`Ctrl+Shift+P` / `Cmd+Shift+P`)
3. 「Reopen in Container」を実行
4. VS Code がコンテナを構築し、接続するまで待機

初回起動時は 5-10 分程度かかります。

## プロジェクト構造

```
.
├── .devcontainer/
│   ├── devcontainer.json              # Dev Container設定
│   ├── docker-compose.devcontainer.yml # オーバーライド設定
│   ├── post-create.sh                  # 初期セットアップスクリプト
│   ├── dev-setup.sh                    # 手動セットアップスクリプト
│   └── .devcontainer.env               # 環境変数
├── docker-compose.yml                  # Docker Compose設定
├── frontend.Dockerfile                 # フロントエンド用Dockerfile
├── backend/
│   ├── Dockerfile                      # バックエンド用Dockerfile
│   ├── pyproject.toml                  # Poetry依存関係
│   └── main.py                         # FastAPI エントリーポイント
└── src/
    └── ... (React フロントエンド)
```

## サービス

### フロントエンド (Node.js/React)

- **ポート**: 3000
- **URL**: http://localhost:3000
- **コマンド**: `npm start`

### バックエンド (FastAPI/Python)

- **ポート**: 8000
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **コマンド**: `poetry run uvicorn main:app --reload`

### データベース (MySQL)

- **ポート**: 3306
- **ホスト**: localhost または db（コンテナ内）
- **ユーザー**: devuser
- **パスワード**: devpass123
- **データベース**: calendar_db

### PHPMyAdmin

- **ポート**: 8080
- **URL**: http://localhost:8080
- **ユーザー**: devuser
- **パスワード**: devpass123

## 環境変数

`.env` ファイルをプロジェクトルートに作成して設定します:

```env
# Frontend
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
REACT_APP_BACKEND_URL=http://localhost:8000

# Backend
DATABASE_URL=mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=your-super-secret-dev-key
```

## よく使うコマンド

### コンテナ管理

```bash
# コンテナを起動
docker-compose up -d

# コンテナを停止
docker-compose down

# コンテナを再構築して起動
docker-compose up -d --build

# ログを表示
docker-compose logs -f [service]

# 特定のサービスのログ
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db
```

### フロントエンド開発

```bash
# コンテナ内に入る
docker-compose exec frontend bash

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm start

# ビルド
npm run build

# テスト実行
npm test
```

### バックエンド開発

```bash
# コンテナ内に入る
docker-compose exec backend bash

# 依存関係をインストール
poetry install

# 開発サーバーを起動
poetry run uvicorn main:app --reload

# テスト実行
poetry run pytest
```

### データベース

```bash
# MySQLコンテナに接続
docker-compose exec db mysql -u devuser -p calendar_db

# PHPMyAdmin でアクセス
# URL: http://localhost:8080
# ユーザー: devuser
# パスワード: devpass123
```

## VS Code の便利な機能

### コンテナ内でのデバッグ

1. `backend/main.py` に breakpoint を設定
2. Run and Debug ビュー（Ctrl+Shift+D）を開く
3. デバッグを開始

### ターミナル

VS Code の統合ターミナルは自動的にコンテナ内で動作します:

```bash
# コンテナ内で実行される
npm install
poetry add package-name
```

### エクステンション

Dev Container で推奨エクステンションが自動的にインストール:

- Python
- Black Formatter
- Pylance
- ESLint
- Prettier
- GitLens
- Docker
- Markdown All in One

## トラブルシューティング

### ポートが既に使用されている

```bash
# ポート使用状況を確認
netstat -ano | findstr :3000

# Windows で PID をキルする
taskkill /PID <PID> /F
```

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# コンテナを完全に削除して再構築
docker-compose down -v
docker-compose up -d --build
```

### 依存関係のインストール失敗

```bash
# キャッシュをクリア
docker system prune -a

# 再構築
docker-compose up -d --build --no-cache
```

### データベース接続エラー

```bash
# MySQL コンテナが起動しているか確認
docker-compose ps

# MySQL ヘルスチェック
docker-compose exec db mysqladmin ping -udevuser -pdevpass123
```

## 開発フロー

1. **機能開発**
   ```bash
   git checkout -b feature/your-feature
   # ファイルを編集
   npm start  # または poetry run uvicorn main:app --reload
   ```

2. **テスト**
   ```bash
   npm test   # フロントエンド
   poetry run pytest  # バックエンド
   ```

3. **コミット**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

4. **プッシュ**
   ```bash
   git push origin feature/your-feature
   ```

## リモート開発時の注意

Dev Container でのリモート開発では:

- ローカルホスト `localhost` は コンテナ内のマシン
- ホストマシンへのアクセスには特別な設定が必要
- Port Forwarding は自動的に行われます

## 追加リソース

- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Dev Containers Specification](https://containers.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## 質問・問題報告

問題が発生した場合:

1. ログを確認: `docker-compose logs`
2. コンテナ状態を確認: `docker-compose ps`
3. `.devcontainer/post-create.sh` のログを確認
4. 必要に応じて再構築: `docker-compose up -d --build`
