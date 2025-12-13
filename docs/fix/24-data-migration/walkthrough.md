# データ移行と不具合修正

## 概要
脚本テーブルへの `public_terms`, `public_contact` カラム追加のマイグレーション漏れ、プロジェクト公開設定(`is_public`)の同期不具合、および**UIからの誤操作を防ぐための改善**を実施しました。

## 実施内容

### 1. DBマイグレーション修正
- `backend/apply_migration.py` を修正し、複数のSQLファイル (`migration_add_public_cols.sql`, `migration_add_project_is_public.sql`) を順次適用するように変更。
- これにより `UndefinedColumnError` が解消されました。

### 2. プロジェクト公開設定の同期修正
- `backend/src/services/script_processor.py` を修正。
- 脚本アップロード時に `TheaterProject.is_public` を更新するロジックを、ORMを使用した明示的な更新処理 (`project.is_public = is_public; db.add(project)`) に変更し、確実にDBへ反映されるようにしました。

### 3. [UI改善] 脚本アップロード画面の初期値設定
- `frontend/src/features/scripts/pages/ScriptUploadPage.tsx` を修正。
- 画面を開いた際、既存のプロジェクト/脚本設定を取得し、**「全体公開」チェックボックス等の状態を自動的に反映**するようにしました。
- これにより、再アップロード時に意図せず「非公開」に戻してしまい、プロジェクト数制限に引っかかる事故を防止します。

## 確認方法
1. デプロイ完了後、対象のプロジェクトを開く。
2. 脚本アップロード画面に進む。
3. **「全体公開にする」チェックボックスが、現在の設定通りになっているか**確認する（以前は常にOFFでした）。
4. そのまま（必要ならチェックを入れて）アップロードし、プロジェクト一覧に戻る。
5. 新しいプライベートプロジェクトを作成し、制限エラーが発生しないことを確認する。
