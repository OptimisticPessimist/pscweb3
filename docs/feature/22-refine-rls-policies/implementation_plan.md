# 実装計画: RLSポリシーの最適化

## 1. 現状確認
現在、ほぼ全てのテーブルに対して以下のポリシーが設定されている：
```sql
CREATE POLICY "Enable all access" ON public.<table> FOR ALL USING (true) WITH CHECK (true)
```
これに対し、Supabase リンターは `UPDATE`, `DELETE`, `INSERT` に対する `true` 許可を警告している（`SELECT` の `USING (true)` は許容される）。

## 2. 修正方針
- `FOR ALL` ポリシーを廃止し、操作を限定したポリシーに変更する。
- 原則として `FOR SELECT USING (true)` のみを残す。これにより、API経由でのデータ閲覧は引き続き可能だが、改ざんは不可能になる。
- バックエンドの FastAPI は DB オーナー権限（または `BYPASSRLS` 権限を持つユーザー）で接続しているため、この変更によるバックエンドへの影響はない。

## 3. 実装手順
1. Alembic マイグレーションを生成する：
   `uv run alembic revision -m "restrict rls policies to select only"`
2. マイグレーションファイルの中で以下のループ処理を記述する：
   - 全対象テーブル（`reservations` を含む）に対し、既存の "Enable all access" ポリシーを削除。
   - `FOR SELECT` のみの新しいポリシー "Allow public read-only access" を作成。
3. `alembic_version` はマイグレーション管理用であるため、特にポリシーを設定しない（API経由でのアクセスを遮断）。

## 4. 対象テーブルリスト
- `project_members`
- `theater_projects`
- `users`
- `notification_settings`
- `project_invitations`
- `scripts`
- `audit_logs`
- `milestones`
- `attendance_events`
- `attendance_targets`
- `scenes`
- `characters`
- `scene_charts`
- `rehearsal_schedules`
- `scene_character_mappings`
- `character_castings`
- `lines`
- `rehearsals`
- `rehearsal_scenes`
- `rehearsal_participants`
- `rehearsal_casts`
- `reservations`
- `alembic_version`

## 5. リスク・留意点
- フロントエンドから直接 Supabase クライアントを使用して `insert` 等を行っている箇所がないか念のため確認する。
  - プロジェクトの設計上、すべての書き込みは `/api/...` の FastAPI エンドポイントを経由しているはずである。
