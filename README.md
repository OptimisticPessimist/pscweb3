# PSC Web 3 - 演劇制作管理システム

FastAPI + PostgreSQL + Azure Functions を使用した演劇制作管理システムです。

## 機能

- Fountain形式の脚本管理
- 香盤表自動生成
- 稽古スケジュール管理
- Discord連携通知
- ダブルキャスト対応

## 前提条件

- **Python 3.13+**
- **Node.js 20+**
- **uv** (Pythonパッケージ管理ツール)

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository_url>
cd pscweb3-1
```

### 2. 環境変数設定 (.env)

ルートディレクトリに `.env` ファイルを作成し、以下の値を設定してください。

```ini
# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# Discord Integration
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:5173/auth/callback
DISCORD_BOT_TOKEN=your_bot_token

# Authentication
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. バックエンド (Backend)

ルートディレクトリで実行します。

```bash
# 依存関係のインストール
uv sync

# データベースマイグレーション
uv run alembic upgrade head

# 開発サーバー起動
uv run uvicorn src.main:app --reload
```
バックエンドは `http://localhost:8000` で起動します。

### 4. フロントエンド (Frontend)

`frontend` ディレクトリで実行します。

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev
```
フロントエンドは `http://localhost:5173` で起動します。

## 開発ガイド

### コードチェック (Backend)

```bash
# Ruffリント
uv run ruff check src/

# 型チェック
uv run python -m typos src/

# フォーマット
uv run ruff format src/
```

### テスト実行 (Backend)

```bash
uv run pytest
```

## トラブルシューティング

### 500 Internal Server Error: `can't subtract offset-naive and offset-aware datetimes`
データベースのカラム定義が Naive DateTime（タイムゾーンなし）であるのに対し、タイムゾーン付き（Aware）の datetime オブジェクトを保存しようとすると発生します。
**対処法**: バックエンド側で保存前に `.replace(tzinfo=None)` を行い、UTCのNaive時刻に変換してください。

## デプロイ

Azure Functions へのデプロイは GitHub Actions で自動化されています。

## ライセンス

MIT
