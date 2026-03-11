
# 実装計画: 台本アップロード時の500エラー修正

## 現状の課題
1. **フィールド名の不一致**:
   - バックエンド: `@router.post("/{project_id}/upload") async def upload_script(file: UploadFile = File(...))` 
     -> `file` という名前のフィールドを期待。
   - フロントエンド: `formData.append('script_file', data.file[0])` 
     -> `script_file` という名前で送信している。
   - これが原因で 422 Unprocessable Entity が発生し、一部の環境では 500 と誤認されたり、例外に繋がったりする可能性がある。

2. **デコード処理の脆弱性**:
   - `fountain_text = file_content.decode("utf-8")` が `try` ブロックの外にあり、Shift_JIS などでエンコードされたファイルが来ると `UnicodeDecodeError` を投げて 500 エラーになる。

3. **Fountain パーサーの脆弱性**:
   - `fountain` ライブラリ内部で `IndexError: string index out of range` が発生する可能性がある（`check_upload_debug.log` の過去の記録より）。

## 修正方針
1. **バックエンド (api/scripts.py)**:
   - フィールド名を `script_file` に変更し、古いクライアント（ある場合）のために `file` をエイリアスとしてサポート。
   - デコード処理を `try-except` 内に入れ、`utf-8-sig` (BOM対応) およびエラー時に `charset-normalizer` での自動判別を行うように改善。
   - デコード失敗時は `400 Bad Request` で適切なメッセージを返す。

2. **フロントエンド (features/scripts/components/ScriptUploadModal.tsx)**:
   - フィールド名が `script_file` であることを再確認し、バックエンドの変更と整合性を取る（現在は `script_file` なので、バックエンドをこれに合わせる）。

3. **バリデーションの強化**:
   - アップロード前にファイルが空でないか、`fountain` 形式として最小限成立するかを確認する。

## 変更予定ファイル
- `backend/src/api/scripts.py`
- `backend/src/services/fountain_parser.py` (必要に応じて前処理の強化)

## 検証項目
- Shift_JIS エンコードの台本がエラーなくアップロード・解析できること。
- UTF-8 (BOMあり) の台本がエラーなくアップロード・解析できること。
- 未認証や権限なしの場合の適切なエラーハンドリング。

## スケジュール
1. `backend/src/api/scripts.py` の修正
2. `fountain_parser.py` の修正（前処理の強化）
3. 動作確認 & テスト実行
4. コードレビュー
