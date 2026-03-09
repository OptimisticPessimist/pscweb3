# Supabase RLS警告の修正

過剰に許可されているRLSポリシー（`FOR ALL USING (true)`）が原因でSupabaseのLinterが警告を出している問題を修正します。

## Proposed Changes

### Database Migration

#### [NEW] [ce7cc9d0b71f_fix_rls_policies_for_schedule_polls.py](file:///f:/src/PythonProject/pscweb3-1/backend/alembic/versions/ce7cc9d0b71f_fix_rls_policies_for_schedule_polls.py)

以下のテーブルのRLSポリシーを修正します：
- `schedule_polls`
- `schedule_poll_candidates`
- `schedule_poll_answers`

修正内容：
1. 既存の `"Enable all access"` ポリシーを削除します。
2. 参照（`SELECT`）のみを許可する `"Enable read access for all"` ポリシーを追加します。
   - `USING (true)` を使用しますが、`SELECT` のみの場合は警告の対象外です。
3. `INSERT`, `UPDATE`, `DELETE` についてはパブリックなポリシーを設定しません。
   - これにより、`anon` や `authenticated` ロールによる直接の書き込みは拒否されます（デフォルトの振る舞い）。
   - バックエンド（`postgres` ロール等）は RLS をバイパスするため、引き続き操作可能です。

## Verification Plan

### Automated Tests
1. マイグレーションの適用テスト
   - `alembic upgrade head` が正常に終了することを確認します。
2. 機能テスト
   - 既存の日程調整機能（作成、表示、回答）が正常に動作し続けることを確認します。

### Manual Verification
1. Supabaseダッシュボード（またはLinterツール）で警告が解消されていることを確認します（ユーザーに依頼）。
