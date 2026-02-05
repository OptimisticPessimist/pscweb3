# PDF設定：タイトルの太字化

## ゴール
PDF出力される台本のタイトルを太字（Bold）にする。

## 変更内容
### `backend`
#### [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
- `CustomPageMan` クラスの以下のメソッドを変更する:
    - `_draw_line(self, l_idx, text, indent=None, is_bold=False)`: `is_bold` 引数を追加。Trueの場合、`setTextRenderMode(2)` (Fill+Stroke) と `setLineWidth` を使用して擬似的に太字を描画する。
    - `_draw_lines(self, l_idx, lines, indent=None, first_indent=None, is_bold=False)`: `is_bold` 引数を追加し、`_draw_line` に渡す。
    - `draw_title(self, l_idx, ttl_line)`: `_draw_lines` 呼び出し時に `is_bold=True` を渡す。
- **補足**:
    - フォントファイル（ `ShipporiMincho` 等）にBoldウェイトが含まれていない、または標準CIDフォント（`HeiseiMin-W3`）がデフォルトであることを考慮し、フォント切替ではなく `setTextRenderMode` による擬似太字（Fake Bold）を採用する。
    - 線の太さは `font_size * 0.03` 程度を目安とする（視認性を確認して調整）。

## 検証計画
### 自動テスト
- 既存の `tests/unit/test_pdf_generator.py` を実行し、リグレッションがないことを確認する。
- **注記**: PDFの描画内容（太字かどうか）を厳密にテストするコードは複雑になるため、目視検証を主とする。

### 手動検証
- 検証用スクリプト `verify_bold_title.py` を作成し、ローカルで実行する。
- 生成された `verification_output.pdf` を開き、タイトル部分が太字になっていることを目視で確認する。
- 比較として、標準（太字なし）のテキストとの差異を確認する。
