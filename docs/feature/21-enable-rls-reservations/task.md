# タスク: reservationsテーブルのRLS有効化

## 概要
Supabaseから `public.reservations` テーブルにRow Level Security (RLS) が有効になっていないという警告が出ているため、RLSを有効にし、適切なポリシーを設定する。

## 詳細
- `reservations` テーブルに対して RLS を有効にする。
- 既存のテーブルと同様に、現在は全てのアクセスを許可するポリシー ("Enable all access") を追加する。
- Alembicマイグレーションスクリプトを作成して実行する。

## 完了条件
- [ ] `reservations` テーブルの RLS が有効になっている。
- [ ] `reservations` テーブルに "Enable all access" ポリシーが設定されている。
- [ ] マイグレーションが正常に適用される。
