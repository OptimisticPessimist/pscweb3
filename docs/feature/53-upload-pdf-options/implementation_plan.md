# 実装計画 - 脚本アップロード時のPDFレイアウト設定追加

## 概要
脚本をアップロードする際にも、PDFの出力設定（用紙の向き：縦/横、文字方向：縦書き/横書き）を選択できるようにし、その設定を保存するように拡張します。これにより、ダウンロード時に毎回設定し直す手間を省きます。

## 変更内容

### 1. データベース (backend)
- `Script` モデル (`src/db/models.py`) に以下のカラムを追加します：
  - `pdf_orientation`: 用紙の向き (`landscape` / `portrait`)
  - `pdf_writing_direction`: 文字方向 (`vertical` / `horizontal`)

### 2. サービス層 (backend)
- `src/services/script_processor.py` の `get_or_create_script` および `process_script_upload` を更新し、上記設定を保存するようにします。

### 3. API (backend)
- `src/api/scripts.py` の `upload_script` エンドポイントを更新し、新しい設定項目をリクエストから受け取るようにします。
- `download_script_pdf` エンドポイントを更新し、クエリパラメータが提供されない場合は保存されている設定値をデフォルトとして使用するようにします。

### 4. フロントエンド
- `frontend/src/features/scripts/api/scripts.ts`: `uploadScript` の引数を更新し、新しい設定値を送信するようにします。
- `frontend/src/features/scripts/pages/ScriptUploadPage.tsx`:
  - 設定選択用のUIを追加します。
  - 初期値として、既存の脚本がある場合はその設定を引き継ぐようにします。

### 5. 多言語対応
- 既に追加されている翻訳キーを確認・利用します。

## 検証計画
### 1. 手動テスト
- 脚本アップロード画面でレイアウトオプションが表示されることを確認。
- オプションを選択してアップロードし、正常に完了することを確認。
- アップロード後、ダウンロードボタンをクリックした際の初期設定が、アップロード時に選択したものになっていることを確認。

### 2. 回帰テスト
- 既存のダウンロード機能が壊れていないことを確認。
