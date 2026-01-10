# Dev Container Setup - クイックスタートガイド

## 📋 必要な準備

### 1. ツールのインストール

- **Docker Desktop** - https://www.docker.com/products/docker-desktop
  - Windows: Docker Desktop for Windows
  - Mac: Docker Desktop for Mac

- **Visual Studio Code** - https://code.visualstudio.com/

- **VS Code 拡張機能: Remote - Containers**
  - VS Code を開く
  - 拡張機能マーケットプレイス (`Ctrl+Shift+X`)
  - 「Remote - Containers」を検索してインストール
  - または: `ms-vscode-remote.remote-containers`

### 2. Docker の起動確認

```bash
# ターミナルで以下を実行
docker --version
docker-compose --version
```

両方ともバージョン表示されれば OK。

## 🚀 Dev Container の起動

### 方法 1: VS Code UI（推奨）

1. **VS Code でプロジェクトフォルダを開く**
   ```bash
   code .
   ```

2. **Command Palette を開く**
   - Windows/Linux: `Ctrl+Shift+P`
   - Mac: `Cmd+Shift+P`

3. **コマンドを実行**
   ```
   Remote-Containers: Reopen in Container
   ```

4. **完了を待つ**
   - 初回は 5-10 分程度
   - ビルド完了後、自動的に接続

### 方法 2: 手動セットアップ

```bash
# ターミナルでプロジェクトディレクトリに移動
cd c:\Users\kirby\Documents\schedule-coordinator-bot

# コンテナをビルド・起動
docker-compose up -d --build

# ログを確認
docker-compose logs -f
```

## ✅ セットアップの確認

### サービスの状態確認

```bash
# すべてのコンテナが起動しているか確認
docker-compose ps

# 出力例:
# NAME              STATUS
# calendar-frontend   Up (healthy)
# calendar-backend    Up (healthy)
# calendar-db         Up (healthy)
```

### ブラウザでアクセス

| サービス | URL | 用途 |
|---------|-----|------|
| フロントエンド | http://localhost:3000 | React アプリ |
| バックエンド API | http://localhost:8000 | FastAPI |
| API ドキュメント | http://localhost:8000/docs | Swagger UI |
| PHPMyAdmin | http://localhost:8080 | DB 管理 |

## 🛠️ 開発方法

### フロントエンド開発

**VS Code ターミナルで:**

```bash
# 開発サーバー起動（自動ホットリロード）
npm start

# ブラウザで確認
# http://localhost:3000
```

### バックエンド開発

**VS Code ターミナルで:**

```bash
# バックエンドコンテナに接続
docker-compose exec backend bash

# 開発サーバー起動（自動リロード）
poetry run uvicorn main:app --reload

# ブラウザで確認
# http://localhost:8000/docs
```

## 📝 環境変数の設定

### .env ファイルを作成

プロジェクトルートに `.env` ファイルを作成:

```env
# Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
REACT_APP_BACKEND_URL=http://localhost:8000

# Backend (内部用)
DATABASE_URL=mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=your-secret-key
```

## 🐛 よくある問題と解決方法

### 問題 1: ポートが既に使用されている

```bash
# 原因を調査
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# 既存のコンテナを停止
docker-compose down

# ポート競合があれば、別のポートを使用
docker-compose -e "FRONTEND_PORT=3001" up -d
```

### 問題 2: データベース接続エラー

```bash
# MySQL が起動しているか確認
docker-compose ps db

# ログを確認
docker-compose logs db

# 完全にリセット
docker-compose down -v
docker-compose up -d --build
```

### 問題 3: npm/poetry インストール失敗

```bash
# キャッシュをクリア（フロントエンド）
docker-compose exec frontend bash
npm cache clean --force
npm install

# キャッシュをクリア（バックエンド）
docker-compose exec backend bash
rm -rf ~/.cache/pip
poetry install
```

### 問題 4: "Cannot connect to Docker daemon"

```bash
# Docker Desktop が起動しているか確認
# Windows: タスクバーのアイコンを確認
# Mac: メニューバーのアイコンを確認

# Docker Desktop を再起動してから再度実行
```

## 📊 ログの確認

```bash
# すべてのサービスのログ
docker-compose logs -f

# 特定のサービス
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db

# 最後の N 行
docker-compose logs --tail=50

# タイムスタンプ付き
docker-compose logs -f --timestamps
```

## 🧹 クリーンアップ

### 一時停止

```bash
# コンテナを停止（データは保持）
docker-compose stop
```

### 完全削除

```bash
# コンテナを停止・削除
docker-compose down

# ボリュームも削除（データベースがリセット）
docker-compose down -v

# イメージもクリア
docker-compose down -v --rmi all
```

## 🔄 開発フロー

### 新機能開発

```bash
# 1. ブランチを作成
git checkout -b feature/my-feature

# 2. コンテナで開発
docker-compose up -d
# VS Code でコードを編集
# npm start または poetry run uvicorn...

# 3. テスト
docker-compose exec frontend npm test
docker-compose exec backend poetry run pytest

# 4. コミット
git add .
git commit -m "feat: description"

# 5. プッシュ
git push origin feature/my-feature
```

## 💡 Tips

### VS Code で統合ターミナルを使用

- `Ctrl+` ` ` でターミナルを開く
- 自動的にコンテナ内で実行される
- `npm install` などはコンテナ内で実行

### ホットリロード

- フロントエンド: `npm start` 時に自動リロード
- バックエンド: `poetry run uvicorn --reload` 時に自動リロード
- ファイルを保存するだけで反映

### デバッグ

```bash
# Python デバッグ（VS Code）
# 1. main.py にブレークポイントを設定
# 2. Run and Debug (Ctrl+Shift+D)
# 3. デバッグを開始

# ブラウザ開発者ツール
# Chrome/Edge: F12
# Firefox: F12
# Safari: Cmd+Option+U
```

## 📚 関連ドキュメント

- [.devcontainer/DEVCONTAINER_GUIDE.md](.devcontainer/DEVCONTAINER_GUIDE.md) - 詳細ガイド
- [.devcontainer/DOCKER_CONFIG.md](.devcontainer/DOCKER_CONFIG.md) - Docker 設定詳細
- [README.md](README.md) - プロジェクト概要
- [TEST_CHECKLIST.md](TEST_CHECKLIST.md) - テスト手順

## 🆘 サポート

### よくある質問

**Q: 初回起動が遅い**
- A: Docker イメージをビルドしているため。2回目以降は高速になります。

**Q: コンテナを削除してもいい？**
- A: はい。`docker-compose down -v` で削除しても、`docker-compose up -d` で再構築できます。

**Q: Windows/Mac/Linux で動作は同じ？**
- A: はい。Dev Container を使用することで、プラットフォーム差による問題を排除できます。

**Q: 本番環境では何が変わる？**
- A: 環境変数、ポート設定、リソース制限などが異なります。`docker-compose.prod.yml` を別途作成します。

## 🎓 学習リソース

- [Docker 公式ドキュメント](https://docs.docker.com/)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Dev Container 仕様](https://containers.dev/)
- [FastAPI チュートリアル](https://fastapi.tiangolo.com/tutorial/)
- [React ドキュメント](https://react.dev/)

---

**準備完了！開発を始めましょう！** 🎉
