# フロントエンド実装: レイアウトとルーティング

## 概要
アプリケーションの基盤となるレイアウト（サイドバー、ヘッダー）と、プロジェクトごとのルーティング構造を実装しました。
実装中に発生したAPIエラーやルーティングの問題も解決済みです。

## 変更点

### 新規コンポーネント
- **[AppLayout.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/layouts/AppLayout.tsx)**: アプリケーション全体のレイアウトコンテナ。サイドバーとヘッダーを含み、メインコンテンツエリアを管理します。
- **[Sidebar.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/components/layout/Sidebar.tsx)**: プロジェクトおよび共通機能をナビゲートするサイドバー。
- **[ProjectDetailsPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/ProjectDetailsPage.tsx)**: プロジェクト概要ページ。サブ機能（Scripts等）への導入として機能します。

### ルーティング・API修正
- **[App.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/App.tsx)**: プロジェクトサブ機能（`/projects/:id/scripts` 等）のルート定義を追加。
- **[src/api/projects.py](file:///f:/src/PythonProject/pscweb3-1/src/api/projects.py)**: `ProjectResponse` スキーマに `role`, `created_at` 等の不足フィールドを追加し、フロントエンドの型と一致させました。
- **[src/dependencies/auth.py](file:///f:/src/PythonProject/pscweb3-1/src/dependencies/auth.py)**: 認証トークンの取得元をクエリパラメータから `Authorization` ヘッダーに変更し、422エラーを解消しました。

## トラブルシューティング完了事項

1. **プロジェクト作成時のAPIエラー (422 Unprocessable Entity)**
   - 原因: APIがトークンをクエリパラメータ(`?token=...`)で期待していたが、フロントエンドはヘッダー(`Authorization: Bearer ...`)で送信していた。
   - 対応: `OAuth2PasswordBearer` を使用してヘッダーからトークンを取得するようにバックエンドを変更。

2. **プロジェクト一覧が表示されない**
   - 原因: APIレスポンスに `role` や `created_at` が含まれておらず、フロントエンドでプロパティアクセス時にエラーが発生していた可能性。
   - 対応: APIレスポンススキーマを拡張し、必要なフィールドを全て返却するように修正。

3. **サイドバーリンクが機能しない（Dashboardにリダイレクトされる）**
   - 原因: `App.tsx` に `/projects/:projectId/scripts` などの具体的なルートが定義されておらず、フォールバックルートによりダッシュボードに戻されていた。
   - 対応: 必要なサブルートを全て定義し、一時的なプレースホルダーコンポーネントを接続。

4. **ReferenceError: useLocation is not defined**
   - 原因: `ProjectDetailsPage.tsx` で不要な `useLocation` 呼び出しが残っていた。
   - 対応: 不要な呼び出しを削除。

## 次のステップ
- 脚本管理機能（一覧、アップロード）の実装に進みます。
