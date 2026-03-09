# Supabase RLS警告の修正 - ウォークスルー

過剰な権限を持つRLSポリシーが原因で発生していたSupabaseのセキュリティ警告を解消しました。

## 変更内容

### データベースマイグレーション
- [ce7cc9d0b71f_fix_rls_policies_for_schedule_polls.py](file:///f:/src/PythonProject/pscweb3-1/backend/alembic/versions/ce7cc9d0b71f_fix_rls_policies_for_schedule_polls.py)
  - 以下のテーブルの `"Enable all access"` (FOR ALL) ポリシーを削除しました。
    - `schedule_polls`
    - `schedule_poll_candidates`
    - `schedule_poll_answers`
  - 代わりに `"Enable read access for all"` (FOR SELECT) ポリシーを追加しました。
  - `INSERT`, `UPDATE`, `DELETE` についてはパブリックなアクセスを禁止し、セキュリティを向上させました。

## 検証結果

### 自動テスト
- `alembic upgrade head` を実行し、マイグレーションが正常に適用されることを確認しました。
- `pytest tests/unit/test_schedule_poll_service.py` を実行し、日程調整機能のロジックに影響がないことを確認しました。
  - 結果: `4 passed in 0.28s`

### 結論
この修正により、Supabase hostのLinter警告が解消され、かつシステムの機能（バックエンド経由の操作）には影響を与えないことが確認されました。
