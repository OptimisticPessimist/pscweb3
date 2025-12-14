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

### Script Upload Page UI Fix
- `ScriptUploadPage.tsx` で初期値が空になる問題（トグルがfalseになる）を修正しました。
- `useEffect` を追加し、既存のプロジェクト/脚本設定（公開設定、利用規約、連絡先）を取得してフォームに初期セットするようにしました。

### Project Creation & Deletion Fixes
- **Deletion**: 以前不足していた `DELETE /api/projects/{id}` エンドポイントを実装し、Frontendからの削除リクエストが正常に処理されるようにしました。
- **Creation Limit**: ユーザーが既に非公開プロジェクトを2つ持っている場合でも、新規プロジェクト作成時に「公開プロジェクト」として作成できるようにしました。
    - Dashboardの「新規プロジェクト作成」モーダルに「公開プロジェクトにする」チェックボックスを追加しました。
    - 非公開プロジェクトの上限に達している場合は、警告を表示し、強制的に公開プロジェクトとして作成するように案内（または制御）しました。
- これにより、再アップロード時に意図せず「非公開」に戻してしまい、プロジェクト数制限に引っかかる事故を防止します。

## 確認方法
1. デプロイ完了後、対象のプロジェクトを開く。
2. 脚本アップロード画面に進む。
3. **「全体公開にする」チェックボックスが、現在の設定通りになっているか**確認する（以前は常にOFFでした）。
4. そのまま（必要ならチェックを入れて）アップロードし、プロジェクト一覧に戻る。
5. 新しいプライベートプロジェクトを作成し、制限エラーが発生しないことを確認する。
