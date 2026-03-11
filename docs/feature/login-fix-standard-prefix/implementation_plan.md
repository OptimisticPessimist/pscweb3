# ログイン404エラーの抜本修正 (標準プレフィックスへの回帰)

## 目的
Azure環境で `/api/auth/login` 等が 404 になる問題を修正します。
以前の修正で FastAPI のルーターに `/api` プレフィックスを直接付与し、`host.json` の `routePrefix` を空に設定していましたが、これが Azure Functions の標準的な動作と競合し、環境によって不安定になる原因となっていました。

本計画では、Azure Functions の標準構成（`/api` プレフィックスを Azure 側で処理し、内部の ASGI アプリにはプレフィックスを除いたパスを渡す）に戻し、整合性を確保します。

## ⚠️ ユーザーレビューおよび手動作業が必要な項目
> [!IMPORTANT]
> 1. **Discord Developer Portal および Azure 環境変数**
>    - `DISCORD_REDIRECT_URI` は `https://<app>.azurewebsites.net/api/auth/callback` ( **/api を含む** ) 状態を維持してください。
> 2. **Azure Static Web Apps (Frontend) ビルド設定**
>    - `VITE_API_URL` は `https://<app>.azurewebsites.net` ( **/api を含めない** ) 状態を維持してください。

## 提案される変更

---

### Backend: ルーティング構成の標準化

#### [MODIFY] main.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/main.py)
すべてのルーターの `prefix` から `/api` を削除します。
- `/api/auth` -> `/auth`
- `/api/projects` -> `/projects`
- `/api` -> `""` (空)
- その他、`/api/health` などの個別ルートからも `/api` を削除。

#### [MODIFY] host.json (file:///f:/src/PythonProject/pscweb3-1/backend/host.json)
`"routePrefix": ""` を `"routePrefix": "api"` に変更（または削除し、デフォルトの "api" が使われるようにする）。

#### [MODIFY] config.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/config.py)
デフォルトの `discord_redirect_uri` を `http://localhost:8000/auth/callback` に変更（ローカルで FastAPI に直接アクセスする場合用）。

---

### Frontend: ローカル開発環境の調整

#### [MODIFY] vite.config.ts (file:///f:/src/PythonProject/pscweb3-1/frontend/vite.config.ts)
プロキシ設定に `rewrite` を追加し、ローカルの FastAPI に渡す際に `/api` を削るようにします。

#### [MODIFY] LoginPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/auth/LoginPage.tsx)
ブラウザのリダイレクト時も `/api` を残すことで、Azure のプレフィックス機能を利用するようにします（現状維持）。

## 検証計画

### Automated Tests
- `backend/src/main.py` のシンタックスチェック (`ruff check`).
- `frontend/vite.config.ts` のシンタックスチェック.

### Manual Verification
1. **ローカル**: `npm run dev` で起動し、ログインボタンをクリック。`http://localhost:5173/api/auth/login` が Vite プロキシ経由でバックエンドの `/auth/login` （プレフィックスなし）に到達することを確認。
2. **Azure (デプロイ後)**: `.../api/health` が戻り、ログインボタンが正常に機能することを確認。
