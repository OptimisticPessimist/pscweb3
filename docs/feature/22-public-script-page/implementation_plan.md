# 公開脚本ページとメタデータ追加 実装計画

## 概要
脚本公開機能の強化として、公開時に「使用条件」や「連絡先」を登録できるようにする。
また、公開された脚本を一覧表示する「公開脚本ページ」を新設し、サイドバーの「Apps」セクションからアクセスできるようにする。

## 変更内容

### データベース (Backend)
- `scripts` テーブルに以下のカラムを追加:
  - `public_terms` (Text, nullable): 使用条件（例：上演許可が必要、改変不可など）
  - `public_contact` (String, nullable): 連絡先（例：メールアドレス、Xアカウントなど）
- **マイグレーション**: `alembic` ではなく、直接SQLでカラムを追加する（Azure環境での運用の簡易化のため、またはスタートアップスクリプトで対応）。
  - ※ ユーザー環境に合わせて、`main.py` 起動時または手動でDB更新を行うSQLを用意する。

### バックエンド API (Backend)
1. **アップロード/更新 API (`POST /api/scripts/{project_id}/upload`)**
   - フォームデータとして `public_terms`, `public_contact` を受け取れるように修正。
   - `process_script_upload` サービス関数でこれらの値をDBに保存するように修正。
2. **公開脚本一覧 API (`GET /api/public/scripts`) [NEW]**
   - 全体公開 (`is_public=True`) されている脚本のリストを返す。
   - ページネーション対応（今回は簡易的に全件または直近N件でも可だが、件数が増えることを想定して設計）。
   - レスポンスにはタイトル、著者、アップロード日時、使用条件、連絡先を含める。
3. **公開脚本詳細 API (`GET /api/public/scripts/{script_id}`)**
   - 既存の `GET /api/scripts/{project_id}/{script_id}` は権限チェックがあるため、公開用エンドポイントが必要か、あるいは既存エンドポイントで `is_public` ならアクセス許可するか検討。
   - シンプルにするため、`GET /api/public/scripts/{script_id}` を新設し、内容（Fountainテキスト）とメタデータを返す。閲覧専用。

### フロントエンド (Frontend)
1. **サイドバー (`Sidebar.tsx`)**
   - "Apps" セクションに「公開脚本 (Public Scripts)」リンクを追加。path: `/public-scripts`
2. **公開脚本一覧ページ (`features/public_scripts/pages/PublicScriptsPage.tsx`) [NEW]**
   - 公開脚本をカード形式またはリスト形式で表示。
   - 検索/フィルタ機能（タイトル、著者）。
3. **公開脚本詳細ページ (`features/public_scripts/pages/PublicScriptDetailPage.tsx`) [NEW]**
   - 脚本の内容（縦書きプレビュー）、使用条件、連絡先を表示。
   - 「インポート」ボタンを配置（既存のインポート機能への導線）。
4. **脚本アップロード/編集モーダル (`features/scripts/components/ScriptUploadModal.tsx`)**
   - 「公開する」チェックボックスがONのとき、使用条件・連絡先の入力欄を表示する。

## 検証計画
- DBにカラムが追加されていること。
- アップロード時にメタデータが保存されること。
- 公開脚本一覧ページで、保存した脚本が表示されること。
- 非公開に設定した脚本が表示されないこと。
