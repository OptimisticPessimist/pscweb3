# ログイン404エラーの修正 (標準プレフィックスへの回帰)

## 変更内容
Azure環境で `/api/auth/login` 等が 404 になる問題を修正しました。
以前の修正で FastAPI 側に無理やり `/api` プレフィックスを持たせていた構成を廃止し、Azure Functions の標準的な動作（`/api` を Azure 側で処理し、内部アプリにはプレフィックスなしで渡す構成）に戻しました。

### 1. バックエンドの変更
- **`src/main.py`**: すべてのルーターの `prefix` および個別のエンドポイントから `/api` を削除しました。
- **`host.json`**: `"routePrefix": ""` を `"routePrefix": "api"` (標準値) に戻しました。
- **`src/config.py`**: ローカル開発用の `discord_redirect_uri` を `/api` なしのパスに修正しました。

### 2. フロントエンドの変更
- **`vite.config.ts`**: プロキシ設定に `rewrite: (path) => path.replace(/^\/api/, '')` を追加しました。これにより、フロントエンドからは引き続き `/api/...` でリクエストを送りつつ、ローカルのバックエンドにはプレフィックスなしで到達するように調整しました。

## ユーザー側で必要なアクション
デプロイ後、念のため以下の設定が維持されているか確認してください：

1. **Discord Developer Portal**
   - OAuth2 Redirects に `https://<app-name>.azurewebsites.net/api/auth/callback` が登録されていること（**/api を含む**）。
2. **Azure Functions 環境変数**
   - `DISCORD_REDIRECT_URI` が `https://<app-name>.azurewebsites.net/api/auth/callback` であること（**/api を含む**）。
3. **Azure Static Web Apps (Frontend) 環境変数**
   - `VITE_API_URL` が `https://<app-name>.azurewebsites.net` であること（**末尾に /api を含めない**）。
