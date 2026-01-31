# Walkthrough - Metadata Vertical Layout

表紙のメタデータ表示を、項目ごとに改行して縦に並べるレイアウトに変更しました。これにより情報の視認性を高め、複数行のメモなども適切に表示できるようになりました。

## Changes

### 1. メタデータの縦積みレイアウト
- `pdf_generator.py` を修正し、Date, Rev, Contact, Notes などの全てのメタデータ項目を `\n`（改行）で結合するロジックに変更しました。
- 以前は一部項目を横並び（スペース区切り）にしていましたが、ユーザー要望により完全縦積みに統一しました。

### 2. 複数行項目のサポート
- **Contact** や **Notes** などの項目は、Fountainファイル内で複数回定義（例: `Notes: Line 1` `Notes: Line 2`）することで、改行を保持したまま出力されます。

```text
Author: Name
Date: 2026-02-01
Rev: 1.0
Contact:
090-xxxx-xxxx
email@example.com
Note:
This is a note.
Multi-line supported.
```

## Verification
- `backend/test_metadata_newline.py` を作成し、複数行のメタデータを含むPDF生成テストを実施。
- 出力結果を確認し、意図通りの改行・レイアウトになっていることを検証しました。
