# 実装計画 - RLSの有効化

PostgRESTに公開されているスキーマ内のテーブルで、行レベルセキュリティ（RLS）が有効になっていない場合を検出し、警告を解消するために、`public`スキーマ内のすべてのテーブルでRLSを有効にします。

## ユーザーレビューが必要な事項

> [!IMPORTANT]
> これにより、すべての公開テーブルでRLSが有効になります。ポリシーが定義されていない場合、**スーパーユーザー以外の誰もこれらのテーブルにアクセスできなくなります**。
> アプリケーションユーザー（`postgres`など）は`BYPASSRLS`権限を持っているか、またはポリシーが必要ですか？
> *前提*: バックエンドDBユーザーは所有者またはバイパス権限を持っている、あるいはPostgREST/Supabaseのセキュリティ要件としてRLSが必要であると想定します。
> *現在の対応*: RLSを有効にするマイグレーションを作成します。

## 変更内容

### データベース
#### [NEW] [alembic/versions/xxxx_enable_rls.py](file:///f:/src/PythonProject/pscweb3-1/backend/alembic/versions/xxxx_enable_rls.py)
- 新しいAlembicマイグレーションスクリプトを作成します。
- `upgrade()`関数内で、以下の各テーブルに対して `ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;` を実行します：
    - `alembic_version` (マイグレーションツール管理用ですが、Linterで指摘されたため一応対象とします)
    - `project_members`
    - `theater_projects`
    - `users`
    - `notification_settings`
    - `project_invitations`
    - `scripts`
    - `audit_logs`
    - `milestones`
    - `attendance_events`
    - `scenes`
    - `characters`
    - `scene_charts`
    - `rehearsal_schedules`
    - `scene_character_mappings`
    - `character_castings`
    - `attendance_targets`
    - `lines`
    - `rehearsals`
    - `rehearsal_scenes`
    - `rehearsal_participants`
    - `rehearsal_casts`

## 検証計画

### 自動テスト
- `alembic upgrade head` を実行してマイグレーションを適用します。
- 既存のバックエンドテストを実行し、回帰（アクセス拒否エラー）がないことを確認します。
  - `pytest`

### 手動検証
- テストが通過すれば、スキーマ変更のみなので不要です。
