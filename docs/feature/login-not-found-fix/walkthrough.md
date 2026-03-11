# ログインエラーの修正: Walkthrough

## 変更内容
Azure環境で `/auth/login` エンドポイントが `404 Not Found` になる問題を修正しました。
Azure Functions の仕様、もしくは内部パスルーティングの競合により、空のルートプレフィックス(`""`)設定下でも `/api` 以外のパスが正常に処理されないケースがあるため、認証関連のAPIを `/api/auth` 配下に移動しました。

1. **バックエンドの変更**:
    - `src/main.py` のルーターマウント設定を `prefix="/auth"` から `prefix="/api/auth"` に変更しました。
    - `src/config.py` 内の `discord_redirect_uri` （ローカル開発用デフォルト値）を `http://localhost:8000/api/auth/callback` に更新しました。
    - （ユーティリティスクリプト `check_discord_connect.py` のURIも合わせて修正しました）
2. **フロントエンドの変更**:
    - `src/pages/auth/LoginPage.tsx` および `src/features/projects/pages/InvitationLandingPage.tsx` のリダイレクト先を `${apiUrl}/auth/login` から `${apiUrl}/api/auth/login` に変更しました。

## テスト結果
- バックエンドの静的解析 (`ruff check .`) を実行し、構文に問題がないことを確認しました。
- フロントエンドの `npm run lint` によって、今回のファイル変更が新たなLintエラーを引き起こしていないことを確認しました。

## ユーザー側で必要なアクション
デプロイ環境および関連サービスの連携を復旧・維持するため、以下の作業をお願いします：
1. **Discord Developer Portal**: アプリの設定を開き、`OAuth2 -> General` の `Redirects` に登録されているURLを `.../api/auth/callback` に変更してください。
2. **Azure Functions 環境変数**: アプリケーション設定にて、`DISCORD_REDIRECT_URI` の値を `.../api/auth/callback` に変更してください。
3. （必要に応じて）変更適用後、Azure Function を再起動し、ブラウザでキャッシュをクリアの上ログインをお試しください。
