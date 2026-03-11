# ログインエラーの修正

## 目的
Azure 関数環境において `/auth/login` が 404 (Not Found) となる原因を修正します。
Azure Functions の仕様により、`routePrefix` を空に設定しても `/api/` 以外のパスが正しくルーティングされないケース（または内部サービスと競合するケース）があります。そのため、認証系の API ルーティングを他の API と同様に `/api/auth` に変更し、安全かつ確実に通信できるようにします。

## ⚠️ ユーザーレビューおよび手動作業が必要な項目
> [!IMPORTANT]  
> 今回の修正でバックエンドのルーティングが `/auth/...` から `/api/auth/...` に変わります。それに伴い、デプロイ先(Azure)およびDiscord側の設定変更が必要になります。以下の手順を合わせて実施してください。  
> 
> **1. Discord Developer Portal の設定変更**
> - 対象のDiscord Applicationの [OAuth2] -> [General] 画面を開く。
> - `Redirects` に登録されているURL（例: `https://.../auth/callback`）を `https://.../api/auth/callback` に変更し、Saveする。  
>
> **2. Azure Functions の環境変数変更**
> - Azureポータルの `pscweb3-functions...` 構成（環境変数）画面を開く。
> - `DISCORD_REDIRECT_URI` の値を `https://.../api/auth/callback` に変更して保存する。
> - (必要に応じて関数を再起動する)

## 提案される変更

---

### Backend ルーティングの変更
バックエンドの FastAPI でマウントしている auth のパスを変更します。

#### [MODIFY] main.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/main.py)
- `app.include_router(auth.router, prefix="/auth", tags=["認証"])` を
  `app.include_router(auth.router, prefix="/api/auth", tags=["認証"])` に変更します。

#### [MODIFY] config.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/config.py)
- ローカル環境でのデフォルト値を修正するために、
  `discord_redirect_uri: str = "http://localhost:8000/auth/callback"` を
  `discord_redirect_uri: str = "http://localhost:8000/api/auth/callback"` に変更します。

---

### Frontend リダイレクトの変更
フロントエンドからバックエンドへログイン処理をリクエストするリンク先を変更します。
*(※フロントエンド上の Callback 受け口である React Router のパス `/auth/callback` は変更しない点に注意)*

#### [MODIFY] LoginPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/auth/LoginPage.tsx)
- `window.location.href = \`${apiUrl}/auth/login\`;` を
  `window.location.href = \`${apiUrl}/api/auth/login\`;` に変更します。

#### [MODIFY] InvitationLandingPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/pages/InvitationLandingPage.tsx)
- `window.location.href = \`${apiUrl}/auth/login\`;` を
  `window.location.href = \`${apiUrl}/api/auth/login\`;` に変更します。


## 確認計画 (Verification Plan)

### Automated Tests
- フロントエンドとバックエンドのフォーマットとLintを実行し、文法エラーがないことを確認する (`flake8` や `ruff`, `tsc`)。

### Manual Verification
1. ローカルで FastAPI と Frontend を起動します。
2. フロントエンドのログイン画面にアクセスし、ログインボタンをクリックします。
3. `http://localhost:8000/api/auth/login` にリダイレクトされ、Discord の認証画面が表示されることを確認します。
4. 認証後、フロントエンドに正常にリダイレクトされ、ダッシュボード等の保護されたページが表示されることを確認します。
