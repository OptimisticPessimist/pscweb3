# [メタデータの改行対応・完全縦積み配置]

## 現状の課題
- ユーザーは全てのメタデータ項目（Author, Date, Revなど含む）を**項目ごとに改行**して表示したい。

## Proposed Changes
### Backend
#### [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
- メタデータ生成ロジックを変更する。
- **基本戦略（完全縦積み配置）**:
    - 全ての項目を `Key: Value` の形式で作成し、`\n` で結合する。
    - 順序: Author -> Date -> Draft -> Rev -> Copyright -> Contact -> Notes
- **実装詳細**:
    1. `metadata_parts` リストを作成。
    2. 各キーが存在すればリストに追加:
        - `Author`: `Author: {name}`
        - `Date`: `Date: {date}`
        - `Draft`: `Draft: {date}`
        - `Rev`: `Rev: {rev}`
        - `Copyright`: `(c) {copyright}`
        - `Contact`: `Contact:\n{content}` (改行維持)
        - `Notes`: `Note:\n{content}` (改行維持)
    3. 最終結合: `"\n".join(metadata_parts)`
    - これにより、表紙に全ての情報が縦に並ぶ。改ページロジックは既存のまま（Author行=メタデータ塊の描画後に改ページ）で機能するはずだが、長くなりすぎて1ページに収まらない場合は `PageMan` の改ページ機能が働く。
    - `draw_lines` を使用しているため、自動改ページされると表紙が複数ページになる可能性があるが、それは仕様として許容する（ユーザーが改行を望んでいるため）。

## Verification Plan
- `backend/test_metadata_newline.py` を作成/更新。
- 全てのメタデータを含むデータをテスト。
- 出力PDFで、全ての項目が改行されていることを確認。
