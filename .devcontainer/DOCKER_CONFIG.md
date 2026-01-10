# Dev Container Docker Configuration Guide

## ファイル構成

```
.devcontainer/
├── devcontainer.json                  # VS Code Dev Container メイン設定
├── docker-compose.devcontainer.yml    # Dev Container用 docker-composeオーバーライド
├── post-create.sh                     # コンテナ作成後の初期化スクリプト
├── dev-setup.sh                       # 開発環境マニュアルセットアップスクリプト
├── .devcontainer.env                  # 環境変数テンプレート
├── DEVCONTAINER_GUIDE.md              # Dev Container 開発ガイド
└── DOCKER_CONFIG.md                   # このファイル

docker-compose.yml                     # メイン Docker Compose 設定
frontend.Dockerfile                    # フロントエンド用 Dockerfile
backend/Dockerfile                     # バックエンド用 Dockerfile
db/Dockerfile                          # MySQL 用 Dockerfile
db/init/01-schema.sql                  # MySQL 初期化スクリプト
```

## devcontainer.json の詳細説明

### 基本設定

```json
{
    "name": "Google Calendar Integration - Dev Container",
    "dockerComposeFile": [
        "../docker-compose.yml",
        "docker-compose.devcontainer.yml"
    ],
    "service": "frontend",
    "workspaceFolder": "/workspace"
}
```

| 項目 | 説明 |
|------|------|
| `name` | Dev Container の表示名 |
| `dockerComposeFile` | 使用する Docker Compose ファイル（複数指定可） |
| `service` | VS Code が接続するサービス |
| `workspaceFolder` | コンテナ内のワークスペース パス |

### VS Code カスタマイズ

```json
"customizations": {
    "vscode": {
        "settings": { ... },      // エディタ設定
        "extensions": [ ... ]      // 自動インストール拡張機能
    }
}
```

**推奨エクステンション:**
- `ms-python.python` - Python サポート
- `ms-python.black-formatter` - Black コードフォーマッター
- `esbenp.prettier-vscode` - Prettier フォーマッター
- `dbaeumer.vscode-eslint` - ESLint
- `mhutchie.git-graph` - Git ビジュアライゼーション
- `eamodio.gitlens` - Git 情報表示

### Features

```json
"features": {
    "ghcr.io/devcontainers/features/node:1": { "nodeVersion": "18" },
    "ghcr.io/devcontainers/features/python:1": { "version": "3.11" },
    "ghcr.io/devcontainers/features/git:1": {}
}
```

公式の Dev Container Features が自動的にインストールされます。

### ポート設定

```json
"forwardPorts": [3000, 8000, 3306],
"portAttributes": {
    "3000": { "label": "Frontend (React)" },
    "8000": { "label": "Backend (FastAPI)" },
    "3306": { "label": "MySQL Database" }
}
```

- ホストマシンのポートをコンテナ内のポートにマッピング
- VS Code の Ports パネルで管理可能

## docker-compose.yml の詳細説明

### フロントエンド サービス

```yaml
frontend:
    build:
      context: .
      dockerfile: frontend.Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - .:/workspace              # ソースコードをマウント
      - /workspace/node_modules   # node_modules を分離
    environment:
      REACT_APP_BACKEND_URL: http://localhost:8000
```

- Node.js 18 ベースのコンテナ
- ホットリロード対応
- `node_modules` はコンテナ内に保持

### バックエンド サービス

```yaml
backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
```

- Python 3.11 ベースのコンテナ
- Poetry で依存関係管理
- データベース起動を待機

### データベース サービス

```yaml
db:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: root_devpass
      MYSQL_DATABASE: calendar_db
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
```

- MySQL 8.0
- ヘルスチェック機能
- `db/init/01-schema.sql` で自動初期化

### PHPMyAdmin サービス

```yaml
phpmyadmin:
    image: phpmyadmin:latest
    ports:
      - "8080:80"
```

- http://localhost:8080 でアクセス
- データベースの視覚的管理

## Dockerfile の説明

### frontend.Dockerfile

```dockerfile
FROM node:18-slim

WORKDIR /workspace

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

- Node.js 18 slim イメージ
- npm 依存関係をインストール
- `npm start` で開発サーバー起動

### backend/Dockerfile

```dockerfile
FROM python:3.11-slim

RUN pip install --no-cache-dir poetry

RUN apt-get update && apt-get install -y \
    build-essential \
    libmysqlclient-dev

ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--reload"]
```

- Python 3.11 slim イメージ
- Poetry で依存関係管理
- Uvicorn ホットリロード対応

## post-create.sh スクリプト

Dev Container 作成後、自動的に実行される初期化スクリプト:

```bash
# 1. フロントエンド依存関係インストール
npm install

# 2. バックエンド設定ファイル生成
# pyproject.toml が無い場合は生成

# 3. Poetry インストール（必要な場合）
pip install poetry

# 4. バックエンド依存関係インストール
poetry install

# 5. データベース起動待機
# MySQL が起動するまで最大60秒待機

# 6. .env ファイル自動生成
# 環境変数テンプレートを作成
```

## 開発環境セットアップ フロー

### 最初の起動

1. **VS Code でプロジェクトを開く**
   ```bash
   code .
   ```

2. **「Reopen in Container」を実行**
   - Command Palette: `Ctrl+Shift+P`
   - 「Remote-Containers: Reopen in Container」

3. **自動セットアップ**
   - Docker イメージをビルド
   - コンテナを起動
   - `post-create.sh` を実行

4. **開発開始**
   ```bash
   npm start        # フロントエンド
   poetry run uvicorn main:app --reload  # バックエンド
   ```

### 日常の開発

```bash
# コンテナが起動した状態で VS Code のターミナルを使用
npm install                    # 新しい依存関係を追加
npm start                      # 開発サーバー起動
docker-compose logs -f         # ログ確認
```

## ネットワーク通信

### コンテナ内通信

```
Frontend (http://localhost:3000)
    ↓ API呼び出し
Backend Service (http://backend:8000)  # コンテナ内では service 名
    ↓ DB接続
Database Service (db:3306)
```

### ホストからのアクセス

```
Host Machine (Windows/Mac)
    ↓
localhost:3000/8000/3306 (ポートフォワーディング)
    ↓
Container Services
```

## トラブルシューティング

### エラー: Port already in use

```bash
# ポートを使用しているプロセスを確認
lsof -i :3000        # macOS/Linux
netstat -ano | findstr :3000  # Windows

# プロセスを終了
kill -9 <PID>
```

### エラー: Cannot connect to database

```bash
# MySQL が起動しているか確認
docker-compose ps

# MySQL ヘルスチェック
docker-compose exec db mysqladmin ping -udevuser -pdevpass123

# ログで詳細確認
docker-compose logs db
```

### エラー: Module not found

```bash
# キャッシュをクリアして再インストール
rm -rf node_modules package-lock.json
npm install

# または
rm -rf backend/__pycache__
poetry install --no-cache
```

### エラー: Build fails

```bash
# イメージをキャッシュなしで再構築
docker-compose up -d --build --no-cache

# または完全にクリア
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## 環境変数管理

### 開発時 (.env ファイル)

```env
REACT_APP_GOOGLE_CLIENT_ID=your-dev-client-id
REACT_APP_BACKEND_URL=http://localhost:8000
DATABASE_URL=mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db
```

### Docker Compose で環境変数を設定

```yaml
environment:
  MYSQL_DATABASE: ${MYSQL_DATABASE:-calendar_db}
  MYSQL_USER: ${MYSQL_USER:-devuser}
  MYSQL_PASSWORD: ${MYSQL_PASSWORD:-devpass123}
```

## パフォーマンス最適化

### キャッシュの活用

```dockerfile
# 効率的な Dockerfile
FROM python:3.11-slim
# 変更頻度の低い操作を先に実行
RUN apt-get update && apt-get install -y build-essential
COPY pyproject.toml poetry.lock ./
RUN poetry install
# 頻繁に変更されるコードは最後に
COPY . .
```

### ボリュームのマウント最適化

```yaml
volumes:
  - .:/workspace           # ソースコード
  - /workspace/node_modules # node_modules はコンテナ内に保持
  - /workspace/.env        # .env は同期しない（オプション）
```

## セキュリティ考慮事項

### 開発環境でのシークレット管理

1. **.env ファイルを .gitignore に追加**
   ```
   .env
   .env.local
   .env.*.local
   ```

2. **.env.example を version control に追加**
   ```
   REACT_APP_GOOGLE_CLIENT_ID=xxx
   REACT_APP_BACKEND_URL=http://localhost:8000
   ```

3. **本番環境では別の設定を使用**
   ```bash
   docker-compose -f docker-compose.yml \
                  -f docker-compose.prod.yml up
   ```

## リソース制限

### メモリ制限

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## ロギング

### ログレベル設定

```yaml
environment:
  LOG_LEVEL: DEBUG          # 開発環境
  # LOG_LEVEL: INFO         # 本番環境
```

### ログ確認

```bash
docker-compose logs -f          # すべてのサービス
docker-compose logs -f backend  # 特定のサービス
docker-compose logs --tail=100  # 最後の100行
```

## 関連リソース

- [Dev Container 公式ドキュメント](https://containers.dev/)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Docker Compose リファレンス](https://docs.docker.com/compose/compose-file/)
- [Feature リスト](https://github.com/devcontainers/features)
