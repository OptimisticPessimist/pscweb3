# 修正内容の確認 (Walkthrough)

## 修正の概要
Supabase のリンター警告 `rls_policy_always_true` に対応するため、各テーブルの RLS ポリシーを `FOR ALL` (全許可) から `FOR SELECT` (読み取り専用許可) に変更しました。

## 修正内容
### 1. Alembicマイグレーションの作成
- `9660d389e8f0_restrict_rls_policies_to_select_only.py` を作成しました。
- 以下の処理を実装：
  - 各テーブルの既存ポリシー "Enable all access" を削除。
  - 新規ポリシー "Allow public read access" (`FOR SELECT USING (true)`) を追加。
  - `alembic_version` については全てのポリシーを削除し、API経由のアクセスを遮断。

### 2. 対象テーブル
- `project_members`, `theater_projects`, `users`, `notification_settings`, `project_invitations`, `scripts`, `audit_logs`, `milestones`, `attendance_events`, `attendance_targets`, `scenes`, `characters`, `scene_charts`, `rehearsal_schedules`, `scene_character_mappings`, `character_castings`, `lines`, `rehearsals`, `rehearsal_scenes`, `rehearsal_participants`, `rehearsal_casts`, `reservations`

## 確認事項
- [x] ローカル環境での `alembic upgrade head` の成功。
- [x] ポリシーが `SELECT` 限定になったことで、Supabase のセキュリティ推奨事項に適合。
- [x] バックエンド（FastAPI）からの操作に影響がないこと（DBオーナー権限でバイパスするため）。

## 今後の課題
- さらにセキュリティを強化する場合、`SELECT` についても `authenticated` ロールへの限定や、ユーザーIDに基づいた行制限などの検討が必要ですが、現時点では「公開API経由での改ざん防止」というリンターの指摘を解消することに重点を置いています。
