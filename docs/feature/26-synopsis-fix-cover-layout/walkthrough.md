# Walkthrough - Synopsis Chapter Fix & Metadata Layout

あらすじが第１章としてカウントされてしまう問題の修正と、メタデータの表示レイアウトを横並びに変更しました。

## Changes

### 1. あらすじの章番号除外
- `pdf_generator.py` 内の `custom_psc_to_pdf` 関数を修正しました。
- `# あらすじ` (H1) セクションの場合、`h1_count` をインクリメントせず、スラグラインに番号を出力しないようにしました。
- これにより、次の「# 第一章」などが正しく `1` から始まります。

### 2. メタデータの横並び表示
- 表紙のメタデータ（Author, Date, Draft, Revision等）の区切り文字を改行（`\n`）からワイドスペース（`   `）に変更しました。
- `CustomPageMan` の `draw_author` 処理を変更し、テキストが長くなった場合に途切れないよう、自動折り返し（`_draw_lines`）を使用するようにしました（以前は `_draw_line_bottom` で切り捨てられていた）。

## Verification
- `backend/test_synopsis_fix.py` を使用して検証を実施。
- エラーなくPDFが生成され、ロジック変更が適用されていることを確認しました。
