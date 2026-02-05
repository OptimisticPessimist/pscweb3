# Task: PDFタイトル太字化

- [x] 実装計画作成 (implementation_plan.md) <!-- id: 0 -->
- [ ] 既存テスト実行 (test_pdf_generator.py) <!-- id: 1 -->
- [ ] PDF生成コード修正 (pdf_generator.py) <!-- id: 2 -->
    - `CustomPageMan._draw_line` に `is_bold` オプション追加
    - `CustomPageMan._draw_lines` に `is_bold` オプション追加
    - `CustomPageMan.draw_title` で `is_bold=True` を指定
- [ ] タイトル太字化の検証 <!-- id: 3 -->
    - 手動検証用スクリプト作成 (`verify_bold_title.py`)
    - 生成されたPDFを目視確認 (成果物として保存)
- [ ] 既存テスト再実行 <!-- id: 4 -->
- [ ] ドキュメント作成 (walkthrough.md) <!-- id: 5 -->
