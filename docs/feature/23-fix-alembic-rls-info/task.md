# タスク: alembic_versionテーブルのRLSポリシー明示化

## 概要
Supabase のセキュリティリンターによる `INFO: RLS Enabled No Policy` に対応する。
`alembic_version` テーブルに RLS が有効であるがポリシーが存在しないため、明示的にアクセスを拒否するポリシーを設定し、警告を解消する。

## 詳細
- `alembic_version` テーブルに対し、常に `false` を返すポリシーを追加する。
- これにより、PostgREST (公開API) 経由のアクセスを明示的に遮断しつつ、リンターのメッセージを解消する。

## 完了条件
- [ ] `alembic_version` テーブルに "Explicitly deny all public access" ポリシーが設定されている。
- [ ] Supabase のリンター警告 `rls_enabled_no_policy` が解消される。
- [ ] マイグレーションが正常に適用される。
