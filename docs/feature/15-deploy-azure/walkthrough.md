# Azure Deployment Walkthrough

このドキュメントでは、Azureへのデプロイ手順と検証結果をまとめます。

## 実施した変更

### 1. Backend Configuration
- **`backend/startup.sh`**: Azure App Service用の起動スクリプトを作成。マイグレーション実行とGunicorn起動を行います。
- **`backend/requirements.txt`**: `uv export` を使用して依存関係を固定化。
- **`backend/pyproject.toml`**: `gunicorn` を追加。

### 2. Frontend Configuration
- **`frontend/vite.config.ts`**: ビルド出力先を `dist` に明示的に設定。
- **Lint/Build Fixes**: ビルドエラーを解消するために以下のファイルを修正しました。
  - `frontend/src/App.tsx`: 重複インポートの削除。
  - `frontend/src/types/index.ts`: `ProjectMember` 型定義の修正。
  - `frontend/src/features/staff/pages/StaffPage.tsx`: 未使用インポートの削除。
  - `frontend/src/features/attendance/AttendancePage.tsx`: 未使用インポート、Markdown混入の修正。
  - `frontend/src/features/casting/pages/CastingPage.tsx`: 未使用インポート削除、型エラー修正。
  - `frontend/src/features/scripts/pages/ScriptListPage.tsx`: 未使用インポート削除。
  - `frontend/src/features/scripts/pages/ScriptDetailPage.tsx`: 未使用インポート削除。
  - `frontend/src/features/schedule/components/RehearsalModal.tsx`: 型エラー修正。
  - `frontend/src/features/auth/hooks/useAuth.test.tsx`: Mock型エラー修正。

### 3. CI/CD Pipeline
- **`.github/workflows/azure-deploy.yml`**: GitHub Actionsワークフローを作成。
  - Backend: Azure App Serviceへのデプロイ
  - Frontend: Azure Static Web Appsへのデプロイ

### 4. Documentation
- **`docs/azure_setup.md`**: 詳細なセットアップ手順書を作成。

## 検証結果

- **Frontend Build**: ローカルでの `npm run build` が成功することを確認しました（17件以上のエラーを修正）。
- **Backend Tests**: 既存のテスト環境（`pytest`）には一部Failuresがありますが、デプロイ構成自体は完了しています。

## 次のステップ (User Action)

1. **Azureリソースの作成**: `docs/azure_setup.md` に従い、Azure PortalでリソースとSecretsを作成してください。
2. **Push**: `feature/15-deploy-azure` ブランチ（またはマージ後の `main`）をプッシュし、GitHub Actionsが正常に動作することを確認してください。
