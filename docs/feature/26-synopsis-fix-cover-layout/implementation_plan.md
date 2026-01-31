# [あらすじ・メタデータレイアウト修正]

あらすじが第1章として扱われてしまう問題の修正と、メタデータの横並び表示を実装する。

## Proposed Changes

### Backend
#### [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
- **あらすじの章番号除外**:
    - `custom_psc_to_pdf` 内で `H1` の処理を修正。
    - `in_synopsis` フラグが True の場合（または H1 テキストが "あらすじ" の場合）、`h1_count` をインクリメントせず、スラグラインに番号を付与しない（`number=None`）。
- **メタデータレイアウト変更**:
    - `generate_script_pdf` 内でのメタデータ文字列生成ロジックを変更。
    - 以前の `\n` 区切りから、横並び（スペース区切りやグリッド配置）に変更したいが、`PageMan` は単純なテキスト描画なので、今回は「スペース区切り」または「1行に複数項目を並べる」テキスト形式にする。
    - 例: `Date: 2026-01-29   Draft: 2026-01-30   Revision: 1.0` のように連結する。
    - `Author` 行に全て突っ込むロジックは継続するが、連結文字を `\n` から `   ` (ワイドスペース3つ等) に変更して横長にする。

## Verification Plan
- `backend/test_synopsis_v2.py` を再利用してPDFを生成。
- 章番号が `Synopsis` に付いていないこと、次の `H1` が `1` から始まることを確認。
- 表紙のメタデータが横並びになっていることを確認。
