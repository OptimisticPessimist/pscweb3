# PDF設定：タイトルの太字化 - 変更内容

## 概要
PDF生成時にタイトルを太字で表示するように変更しました。

## 変更ファイル

### 1. `backend/src/services/pdf_generator.py`

#### 変更内容
- `CustomPageMan._draw_line()` メソッドに `is_bold` パラメータを追加
- `CustomPageMan._draw_lines()` メソッドに `is_bold` パラメータを追加
- `CustomPageMan.draw_title()` メソッドで `is_bold=True` を指定

#### 実装詳細
太字の実装には、reportlabの低レベルPDFコマンドを使用しました：
- `canvas._code.append('2 Tr')` でテキストレンダリングモードを「Fill+Stroke」に設定
- `canvas.setLineWidth(font_size * 0.03)` で線の太さを設定
- `saveState()` と `restoreState()` で状態を保存・復元

この方法により、フォントファイルにBoldウェイトが含まれていない場合でも、擬似的に太字を表現できます。

### 2. `verify_bold_title.py` (検証用スクリプト)
手動検証用のスクリプトを作成し、`verification_bold_title.pdf` を生成して目視確認を行いました。

## テスト結果
- ✅ 既存のユニットテスト (`test_pdf_generator.py`) が全て成功
- ✅ 検証用PDFが正常に生成され、タイトルが太字で表示されることを確認

## 技術的な考慮事項
1. **reportlabのAPI制限**: `setTextRenderMode()` メソッドが存在しないため、`_code` リストに直接PDFコマンドを追加する方法を採用
2. **互換性**: `saveState()` / `restoreState()` を使用することで、他のテキスト描画に影響を与えない
3. **線の太さ**: `font_size * 0.03` という係数は、視認性と美観のバランスを考慮して設定
