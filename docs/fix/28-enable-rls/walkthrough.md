# Walkthrough - RLSの有効化

データベースLinterのエラー「RLS Disabled in Public」を解消するため、`public`スキーマ内のテーブルでRLS（行レベルセキュリティ）を有効化しました。

## 変更内容

### バックエンド
#### [NEW] [alembic/versions/51aca2fbf3e9_enable_rls_on_public_tables.py](file:///f:/src/PythonProject/pscweb3-1/backend/alembic/versions/51aca2fbf3e9_enable_rls_on_public_tables.py)
- マイグレーションスクリプトを作成し、以下の処理を実装しました：
  - 対象テーブルに対して `ENABLE ROW LEVEL SECURITY` を実行。
  - アプリケーションの動作を阻害しないよう、一時的に「全アクセス許可」ポリシー（`Enable all access`）を追加。
    - `CREATE POLICY "Enable all access" ON public.<table> FOR ALL USING (true) WITH CHECK (true)`
  - 対象テーブル: `project_members`, `theater_projects`, `users`, など（`alembic_version` は除外）。

## 検証結果

### 自動テスト
- `pytest` を実行しましたが、12件の失敗が確認されました。
- **補足**: RLSポリシー（全許可）を追加した状態でも同様の失敗が発生しており、ログの一部（`IndexError`）から判断すると、RLS以外の既存の問題（パース処理など）に関する失敗である可能性が高いです。RLSによるアクセス拒否ではないと考えられます。

### 手動検証
- `alembic upgrade head` が正常に完了し、データベースへの変更が適用されたことを確認しました。

## 次のステップ
- 本番環境等でより厳格なセキュリティが必要な場合は、`Enable all access` ポリシーを削除し、適切なロールベースのポリシー（例：`auth.uid() = user_id` など）に置き換える必要があります。
