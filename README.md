# PSC Web 3 - 演劇制作管理システム

本アプリはsatamame様の[pscweb2](https://github.com/satamame/pscweb2)を参考に開発しました。

FastAPI + React + PostgreSQL を使用して、演劇制作における台本管理・スケジュール管理・出欠管理を一元化するWebアプリケーションです。

## 📋 概要

PSC Web 3 は、演劇制作における台本管理・スケジュール管理・出欠管理を一元化するWebアプリケーションです。Discord連携により、制作チームとのコミュニケーションを円滑化します。

## ✨ 主な機能

- **📝 脚本管理**: Fountain形式の台本を管理し、シーン情報を自動解析
- **📊 香盤表自動生成**: 台本データから出演者別の香盤表を自動生成
- **📅 スケジュール管理**: 稽古スケジュールの作成・編集・共有
- **✅ 出欠管理**: 稽古への参加状況を管理
- **🎭 ダブルキャスト対応**: 複数キャストパターンに対応した配役管理
- **🔗 Discord連携**: Discord OAuth認証とBot通知機能
- **📁 プロジェクト管理**: 複数公演プロジェクトの管理

## 🛠️ 技術スタック

### バックエンド
- **言語**: Python 3.12+
- **フレームワーク**: FastAPI
- **データベース**: PostgreSQL (Neon)
- **ORM**: SQLAlchemy (非同期)
- **認証**: OAuth 2.0 (Discord)
- **マイグレーション**: Alembic
- **パッケージ管理**: uv

### フロントエンド
- **言語**: TypeScript
- **フレームワーク**: React 19
- **ルーティング**: React Router v7
- **状態管理**: TanStack Query (React Query)
- **UIライブラリ**: Headless UI
- **スタイリング**: Tailwind CSS v4
- **カレンダー**: FullCalendar
- **フォーム**: React Hook Form + Zod
- **ビルドツール**: Vite

### インフラ
- **バックエンド**: Azure Functions (従量課金プラン)
- **フロントエンド**: Azure Static Web Apps
- **データベース**: PostgreSQL (Neon)
- **CI/CD**: GitHub Actions
- **コンテナ**: Docker (ローカル開発環境)

## 📦 前提条件

- **Python 3.12+**
- **Node.js 20+**
- **uv** (Pythonパッケージ管理ツール)
  ```bash
  # Windows
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## 🚀 セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository_url>
cd pscweb3
```

### 2. 環境変数設定

ルートディレクトリに `.env` ファイルを作成してください。

```ini
# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# Discord Integration
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:5173/auth/callback
DISCORD_BOT_TOKEN=your_bot_token

# Authentication
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> [!TIP]
> `.env.example` ファイルをコピーして使用できます。
> ```bash
> cp .env.example .env
> ```

### 3. バックエンドのセットアップ

`backend` ディレクトリで実行します。

```bash
cd backend

# 依存関係のインストール
uv sync


# 開発サーバー起動
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

バックエンドAPIは `http://localhost:8000` で起動します。  
API仕様書は `http://localhost:8000/docs` で確認できます。

### 4. フロントエンドのセットアップ

`frontend` ディレクトリで実行します。

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev
```

フロントエンドは `http://localhost:5173` で起動します。

## 🧪 テスト

### バックエンドテスト

```bash
cd backend

# 全テスト実行 (カバレッジ付き)
uv run pytest

# 特定テストファイルのみ実行
uv run pytest tests/test_attendance.py

# カバレッジレポート確認
# HTMLレポートは htmlcov/index.html に生成されます
```

### フロントエンドテスト

```bash
cd frontend

# テスト実行
npm test

# テスト監視モード
npm test -- --watch
```

## 🔧 開発ガイド

### コードチェック (Backend)

```bash
cd backend

# Ruffリント
uv run ruff check src/

# 自動修正
uv run ruff check --fix src/

# フォーマット
uv run ruff format src/
```

### コードチェック (Frontend)

```bash
cd frontend

# ESLint
npm run lint

# TypeScript型チェック
npm run build
```

### データベースマイグレーション

```bash
cd backend

# 新しいマイグレーションファイル作成
uv run alembic revision --autogenerate -m "migration_message"

# マイグレーション適用
uv run alembic upgrade head

# ロールバック
uv run alembic downgrade -1
```

## 📊 プロジェクト構成

```
pscweb3-1/
├── backend/              # FastAPIバックエンド
│   ├── src/
│   │   ├── api/         # APIエンドポイント
│   │   ├── core/        # コア機能 (設定、認証等)
│   │   ├── models/      # SQLAlchemyモデル
│   │   ├── schemas/     # Pydanticスキーマ
│   │   └── services/    # ビジネスロジック
│   ├── tests/           # テストコード
│   ├── alembic/         # マイグレーション
│   └── pyproject.toml   # Python依存関係
├── frontend/            # Reactフロントエンド
│   ├── src/
│   │   ├── components/  # 共通コンポーネント
│   │   ├── features/    # 機能別コンポーネント
│   │   ├── hooks/       # カスタムフック
│   │   ├── types/       # TypeScript型定義
│   │   └── utils/       # ユーティリティ関数
│   └── package.json     # npm依存関係
└── docs/                # プロジェクトドキュメント
```

## 🐛 トラブルシューティング

### `can't subtract offset-naive and offset-aware datetimes`

**原因**: タイムゾーン付き datetime とタイムゾーンなし datetime の混在  
**対処法**: バックエンド側で保存前に `.replace(tzinfo=None)` を実行

```python
from datetime import datetime, timezone

# 現在時刻をUTC Naive形式に変換
now = datetime.now(timezone.utc).replace(tzinfo=None)
```

### `MissingGreenlet` エラー (テスト時)

**原因**: 非同期SQLAlchemyの設定不足  
**対処法**: `pytest.ini` に `asyncio_mode = "auto"` を設定済み

### uv sync が失敗する

**対処法**: 
```bash
# キャッシュクリア
uv cache clean

# 再度インストール
uv sync
```

## 🚢 デプロイ

### Azure へのデプロイ

本アプリケーションは以下のAzureサービスにデプロイされています：

| サービス | 用途 | URL |
|----------|------|-----|
| **Azure Functions** | バックエンドAPI + Timer Function | `https://pscweb3-functions-*.azurewebsites.net` |
| **Azure Static Web Apps** | フロントエンド (React SPA) | `https://*.azurestaticapps.net` |
| **Neon PostgreSQL** | データベース | - |

#### デプロイ設定

GitHub Actions による CI/CD が設定されています。`main` ブランチへのプッシュで自動デプロイされます。

**必要なGitHub Secrets:**

| シークレット名 | 説明 |
|---------------|------|
| `AZURE_FUNCTIONAPP_NAME` | Function App名 |
| `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` | Function Appの発行プロファイル |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web Appsのデプロイトークン |
| `VITE_API_URL` | Function AppのURL (例: `https://pscweb3-functions-*.azurewebsites.net`) |

**Azure Function App環境変数:**

| 変数名 | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL接続文字列 |
| `JWT_SECRET_KEY` | JWT認証用シークレットキー |
| `DISCORD_CLIENT_ID` | Discord OAuthクライアントID |
| `DISCORD_CLIENT_SECRET` | Discord OAuthクライアントシークレット |
| `DISCORD_BOT_TOKEN` | Discord Bot トークン |
| `DISCORD_REDIRECT_URI` | Discord OAuth リダイレクトURI |
| `FRONTEND_URL` | Static Web AppsのURL |

> [!TIP]
> 詳細なセットアップ手順は [docs/azure_functions_setup.md](docs/azure_functions_setup.md) を参照してください。

## 📝 ドキュメント

詳細なドキュメントは `docs/` ディレクトリを参照してください。

- [実装計画](docs/feature/)
- [バグ修正履歴](docs/bugfix/)
- [コーディング規約](docs/rules/)

## 🤝 コントリビューション

1. フィーチャーブランチを作成: `git checkout -b feature/01-your-feature`
2. 変更をコミット: `git commit -m 'feat: Add some feature'`
3. ブランチにプッシュ: `git push origin feature/01-your-feature`
4. プルリクエストを作成

### コミットメッセージ規約

```
prefix: 理由 (日本語で50文字以内)

詳細説明
- 変更点1
- 変更点2
```

**Prefix一覧**:
- `feat`: 新規機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイル変更
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・ツール変更

## 📄 ライセンス

MIT License
