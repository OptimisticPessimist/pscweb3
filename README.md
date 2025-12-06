# PSC Web 3 - 演劇制作管理システム

FastAPI + PostgreSQL + Azure Functions を使用した演劇制作管理システムです。

## 機能

- Fountain形式の脚本管理
- 香盤表自動生成
- 稽古スケジュール管理
- Discord連携通知
- ダブルキャスト対応

## セットアップ

### 1. 環境変数設定

`.env.example` をコピーして `.env` を作成し、必要な値を設定してください。

```bash
cp .env.example .env
```

### 2. 依存関係インストール

```bash
uv sync
```

### 3. データベースマイグレーション

```bash
uv run alembic upgrade head
```

### 4. 開発サーバー起動

```bash
uv run uvicorn src.main:app --reload
```

## 開発

### コードチェック

```bash
# Ruffリント
uv run ruff check src/

# 型チェック
uv run python -m typos src/

# フォーマット
uv run ruff format src/
```

### テスト実行

```bash
uv run pytest
```

## デプロイ

Azure Functions へのデプロイは GitHub Actions で自動化されています。

## ライセンス

MIT
