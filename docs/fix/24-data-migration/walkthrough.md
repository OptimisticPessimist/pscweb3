# データ移行と不具合修正

## 概要
脚本テーブルへの `public_terms`, `public_contact` カラム追加のマイグレーション漏れ、およびプロジェクト公開設定(`is_public`)の同期不具合を修正しました。

## 実施内容

### 1. DBマイグレーション修正
- `backend/apply_migration.py` を修正し、複数のSQLファイル (`migration_add_public_cols.sql`, `migration_add_project_is_public.sql`) を順次適用するように変更。
- これにより `UndefinedColumnError` が解消されました。

### 2. プロジェクト公開設定の同期修正
- `backend/src/services/script_processor.py` を修正。
- 脚本アップロード時に `TheaterProject.is_public` を更新するロジックにおいて、`TheaterProject` モデルのインポート漏れおよび `db.execute` の挙動による更新失敗（サイレントエラー）が発生していました。
- ORMを使用した明示的な更新処理 (`project.is_public = is_public; db.add(project)`) に変更し、確実にDBへ反映されるようにしました。

## 確認方法
1. デプロイ完了後、公開プロジェクトにて脚本を再度アップロード（上書き）する。
2. その後、新しいプライベートプロジェクトを作成し、制限エラーが発生しないことを確認する。
