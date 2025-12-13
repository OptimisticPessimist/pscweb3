# 公開脚本ページとメタデータ追加 実装完了

## 概要
ユーザーが脚本を公開する際に「使用条件」や「連絡先」を登録できるようにし、公開された脚本を一覧表示する「公開脚本ページ」を実装しました。

## 変更点

### データベース / Backend
- **Schema**: `scripts` テーブルに `public_terms` (Text) と `public_contact` (String) カラムを追加。
  - SQLマイグレーションスクリプト: `backend/migration_add_public_cols.sql`
  - Python適用スクリプト: `backend/apply_migration.py`
  - **重要**: ユーザー環境で `python backend/apply_migration.py` を実行するか、SQLを適用してください。
- **API**:
  - `POST /api/scripts/{project_id}/upload`: 公開条件・連絡先を受け入れるように拡張。
  - `GET /api/public/scripts`: 公開脚本一覧を取得するエンドポイントを新設。
  - `GET /api/public/scripts/{script_id}`: メタデータを含めて脚本詳細を返すように修正。

### Frontend
- **公開脚本一覧**: サイドバーの "Apps" > "Public Scripts" からアクセス可能。
  - URL: `/public-scripts`
  - タイトル、著者、公開条件などをカード形式で表示。
- **公開脚本詳細**:
  - URL: `/public-scripts/:scriptId`
  - 脚本の内容（縦書きプレビュー）とメタデータを表示。
- **脚本アップロード画面**:
  - 「公開する」にチェックを入れると、使用条件と連絡先の入力欄が表示されるように変更。

## 検証手順

1. **DBマイグレーション**
   ```bash
   # バックエンドディレクトリで実行
   python backend/apply_migration.py
   ```
   ※ エラーが出る場合は `postgresql` 接続情報を確認し、必要ならSQLを直接実行してください。

2. **脚本のアップロード（公開設定）**
   - 任意のプロジェクトで脚本アップロード画面へ。
   - 「Public」にチェックを入れる。
   - 「Usage Terms」と「Contact Info」を入力してアップロード。

3. **公開脚本の確認**
   - サイドバーの "Public Scripts" をクリック。
   - アップロードした脚本が表示されることを確認。
   - クリックして詳細画面へ遷移し、メタデータと内容が表示されることを確認。

## 補足
- 既存の公開済み脚本にはメタデータがないため空欄で表示されます。編集は現在アップロード（上書き）のみ対応しています。
