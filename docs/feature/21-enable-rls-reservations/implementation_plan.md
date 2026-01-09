# 実装計画: reservationsテーブルのRLS有効化

## 1. 現状確認
- `reservations` テーブルは `26dbc6dee525` マイグレーションで追加された。
- 以前の `51aca2fbf3e9` マイグレーションでは、既存の全てのテーブルに対して RLS を有効にしたが、`reservations` は後から追加されたため対象外となっていた。

## 2. 修正方針
- 新しいAlembicマイグレーションスクリプトを作成する。
- `upgrade` 関数内で以下を実行する:
  - `ALTER TABLE public.reservations ENABLE ROW LEVEL SECURITY`
  - `CREATE POLICY "Enable all access" ON public.reservations FOR ALL USING (true) WITH CHECK (true)`
- `downgrade` 関数内で以下を実行する:
  - `DROP POLICY "Enable all access" ON public.reservations`
  - `ALTER TABLE public.reservations DISABLE ROW LEVEL SECURITY`

## 3. 実装手順
1. `alembic revision -m "enable rls for reservations"` を実行してマイグレーションファイルを生成する。
2. 生成されたファイルに RLS 有効化のロジックを記述する。
3. ローカル環境でマイグレーションをテストする（可能であれば）。

## 4. リスク・留意点
- RLSを有効にすると、ポリシーがない限りアクセスできなくなるため、必ずポリシーを同時に作成する。
- 今回は既存の他テーブルに合わせて "Enable all access" (全許可) とする。
