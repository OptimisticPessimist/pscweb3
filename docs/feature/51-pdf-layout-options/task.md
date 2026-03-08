# タスク #51: PDF出力レイアウトオプション

## 概要
台本のPDF出力時に、A4用紙の向き（縦/横）と文字方向（縦書き/横書き）を選択できるようにする。

## タスクリスト

- [ ] 1. バックエンド: `pdf_generator.py` に横書きPDF生成クラス `HorizontalPageMan` を追加
- [ ] 2. バックエンド: `generate_script_pdf()` に `orientation` と `writing_direction` パラメータを追加
- [ ] 3. バックエンド: PDFダウンロードAPI (`scripts.py`) にクエリパラメータ追加
- [ ] 4. バックエンド: Discord通知サービスの `script_notification.py` も対応（デフォルトのまま）
- [ ] 5. フロントエンド: `scripts.ts` API関数にクエリパラメータ追加
- [ ] 6. フロントエンド: `ScriptDetailPage.tsx` にPDFオプション選択UI追加
- [ ] 7. フロントエンド: `ScriptListPage.tsx` にPDFオプション選択UI追加
- [ ] 8. フロントエンド: 5言語の翻訳ファイル更新
- [ ] 9. テスト: PDF生成ユニットテスト更新
- [ ] 10. コードレビュー
