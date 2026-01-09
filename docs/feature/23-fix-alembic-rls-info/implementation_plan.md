# 実装計画: alembic_versionテーブルのRLSポリシー明示化

## 1. 現状確認
前回の修正で `alembic_version` から全許可ポリシーを削除した。
現在：RLS=Enabled, Policy=None
Supabaseリンター：`rls_enabled_no_policy` (INFO)

## 2. 修正方針
- 「常に不許可」のポリシーを明示的に作成する。
```sql
CREATE POLICY "Explicitly deny all public access" ON public.alembic_version FOR ALL USING (false) WITH CHECK (false);
```

## 3. 実装手順
1. Alembic マイグレーションを生成。
2. `alembic_version` に拒否ポリシーを作成。
3. ローカルおよび本番へ適用。

## 4. リスク・留意点
- 特になし。バックエンド（管理者接続）には影響しない。
