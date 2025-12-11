# Azure セットアップ手順

このプロジェクトをAzureにデプロイするための手順です。

## 1. 必要なリソースの作成

### 1-1. Azure App Service (Backend)
1. Azure Portalで **App Services** を検索し、「作成」をクリックします。
2. 以下の設定を行います：
   - **サブスクリプション**: (お使いのサブスクリプション)
   - **リソースグループ**: 新規作成 (例: `rg-pscweb3`)
   - **名前**: ユニークな名前 (例: `pscweb3-backend`)
   - **公開**: コード
   - **ランタイムスタック**: Python 3.12 (または 3.13)
   - **オペレーティングシステム**: Linux
   - **地域**: Japan East (または近い場所)
   - **価格プラン**: **Free F1** (または Basic B1)
     - 「サイズを変更」から「SpecPicker」を開き、Dev/Testタブの F1 を選択します。

3. 作成後、リソースに移動し、**設定 > 環境変数** を設定します：
   - `DATABASE_URL`: NeonのPostgreSQL接続文字列
   - `JWT_SECRET_KEY`: 生成したシークレットキー
   - `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`
   - `AZURE_APP_SERVICE`: `true` (バックエンドコードで認識するため)

4. **デプロイメント センター** 設定はGitHub Actionsで自動設定するか、発行プロファイルを取得します。
   - 今回はGitHub ActionsのSecretに設定するため、**概要** ページの上部にある「**発行プロファイルの取得**」をクリックしてファイルをダウンロードします。
   - ダウンロードしたファイルの中身（XML全体）をコピーします。
   - GitHubリポジトリの **Settings > Secrets and variables > Actions** に移動し、`AZURE_WEBAPP_PUBLISH_PROFILE` という名前で新しいRepository Secretを作成し、値を貼り付けます。

### 1-2. Azure Static Web Apps (Frontend)
1. Azure Portalで **Static Web Apps** を検索し、「作成」をクリックします。
2. 以下の設定を行います：
   - **名前**: ユニークな名前 (例: `pscweb3-frontend`)
   - **プランの種類**: **Free**
   - **デプロイの詳細**: GitHubを選択し、リポジトリとブランチ(`main`)を選択します。
   - **ビルドの詳細**:
     - **ビルドのプリセット**: React (または Custom)
     - **アプリの場所**: `/frontend`
     - **Apiの場所**: (空白)
     - **出力先**: `dist`

3. 作成すると、自動的にGitHub Actionsのワークフローファイルがリポジトリに追加（コミット）される場合がありますが、今回は手動で作成した `.github/workflows/azure-deploy.yml` を使用します。
   - 作成後の **概要** ページで「**デプロイメントトークンの管理**」をクリックし、トークンをコピーします。
   - GitHubリポジトリの **Settings > Secrets and variables > Actions** に移動し、`AZURE_STATIC_WEB_APPS_API_TOKEN` という名前で新しいRepository Secretを作成し、値を貼り付けます。

### 1-3. Neon (Database)
1. Neonコンソールでプロジェクトを作成します。
2. 接続文字列 (`postgres://...`) をコピーします。
3. これを上記の Azure App Service の環境変数 `DATABASE_URL` に設定します。
   - **注意**: `psycopg2` や `asyncpg` で接続する場合、`sslmode=require` が必要になる場合があります。NeonはデフォルトでSSL接続です。

## 2. デプロイの実行

1. 上記の設定（特にSecrets）が完了したら、`main` ブランチにプッシュします。
2. GitHubの **Actions** タブで `Azure Deployment` ワークフローが実行され、成功することを確認します。

## 3. 動作確認

1. Static Web App のURLにアクセスし、画面が表示されるか確認します。
2. ログインを行い、バックエンドへのAPIリクエストが成功するか確認します。
   - 失敗する場合は、ブラウザのコンソールログや、Azure App Serviceのログストリームを確認します。
   - **CORS設定**: バックエンドの `main.py` でCORSを許可していますが、Azure App Service側でもCORS設定が必要な場合があります（基本的にはコード側のミドルウェアで処理されます）。
