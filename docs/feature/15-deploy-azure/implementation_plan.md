# Azureデプロイメント実装計画

## 目的
`pscweb3` アプリケーションを、可能な限り無料枠を使用してAzureにデプロイします。以下の要件に従います：
- **Backend**: Azure App Service (F1 Free Tier)。もしLinux PythonでF1が利用できない場合はB1を検討しますが、まずはF1で進めます。
- **Frontend**: Azure Static Web Apps (Free Tier) または App Service。 **推奨**: パフォーマンスと構成の分離のため、Azure Static Web Appsを採用します。
- **Database**: Neon (Free Tier PostgreSQL)。
- **言語**: Python 3.13 (Azure App Serviceでのサポート状況により3.12になる可能性があります。`pyproject.toml`の`requires-python = ">=3.12"`に準拠します)。

## ユーザーレビュー事項
> [!IMPORTANT]
> **Azure App Service プラン**: Free Tier (F1) にはクォータ制限（60 CPU分/日）があります。これを超えると停止します。常時稼働にはBasic (B1) が推奨されますが、今回はF1で進めます。
> **Pythonバージョン**: Azure App ServiceがPython 3.13を即座にサポートしていない可能性があります。3.12/3.13互換で構成します。
> **データベース**: Neonを使用します。セットアップ時に `DATABASE_URL` の設定が必要です。

## 変更内容

### 設定
#### [NEW] [backend/requirements.txt](file:///F:/src/PythonProject/pscweb3-1/backend/requirements.txt)
- `pyproject.toml` からAzure App Serviceデプロイ用に生成します。

#### [NEW] [backend/startup.sh](file:///F:/src/PythonProject/pscweb3-1/backend/startup.sh)
- Gunicorn/Uvicorn用の起動スクリプトを作成します。

#### [NEW] [.github/workflows/azure-deploy.yml](file:///F:/src/PythonProject/pscweb3-1/.github/workflows/azure-deploy.yml)
- BackendをAzure App Serviceへ、FrontendをAzure Static Web AppsへデプロイするGitHub Actionsワークフローを作成します。

### Backend
#### [MODIFY] [backend/src/main.py](file:///F:/src/PythonProject/pscweb3-1/backend/src/main.py)
- `ProxyHeadersMiddleware` がAzure用に正しく設定されているか確認します（確認済み）。

### Frontend
#### [MODIFY] [frontend/vite.config.ts](file:///F:/src/PythonProject/pscweb3-1/frontend/vite.config.ts)
- ビルド出力ディレクトリが標準の `dist` であり、Static Web Appsで正しく扱えることを確認します。

## 検証計画

### 自動テスト
- `pytest` を実行し、バックエンドの安定性を確認します。
- `npm run build` を実行し、フロントエンドのビルドを確認します。
- GitHub Actionsにより、ビルドとデプロイを自動的に検証します。

### 手動検証
1. **Frontend**: Static Web AppsのURLにアクセスし、ロードとログイン画面を確認します。
2. **Backend**: Azure App ServiceのURLで `/health` エンドポイントにアクセスし確認します。
3. **Integration**: ログインし、Neon DBからデータが取得できることを確認します。
