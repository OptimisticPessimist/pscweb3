# Walkthrough - Synopsis Support & Title Page Layout

演劇台本PDFの表紙（タイトルページ）にあらすじを表示できるようにし、タイトルとメタデータのレイアウトを改善しました。

## Changes

### Backend

#### `backend/src/services/pdf_generator.py`

- **あらすじ（Synopsis）のパース処理を追加**:
    - Fountainヘッダーの `Synopsis:` または `あらすじ:` キーを読み取るようにしました。
    - 読み取ったあらすじはメタデータの一部として扱われます。

- **メタデータの表示位置を変更**:
    - 以前は `TITLE` 行に追記していましたが、タイトルのスタイル（太文字など）に影響を与えないよう、 `AUTHOR` 行に集約するように変更しました。
    - `AUTHOR` 行が存在しない場合は、`TITLE` 行の直後に新規作成して挿入します。
    - これにより、タイトルは太文字で大きく、あらすじやその他のメタデータ（Author, Dateなど）はその下の著者名欄に標準フォントで表示されるようになります。

## Verification Results

### Automated Tests
- `backend/test_synopsis.py` (一時作成) を使用して検証を実施。
- `Synopsis` を含むFountainテキストからPDFがエラーなく生成されることを確認しました。
- ログ出力にてフォントパスの解決やPDF生成サイズが正常であることを確認済。

### Manual Verification
- 実際のPDF出力の目視確認は環境制約上行っていませんが、以下のロジックが正常に動作することを確認しました：
    1. Fountainヘッダーからのメタデータ抽出
    2. `ps_script` オブジェクト内の `AUTHOR` 行へのテキスト置換/挿入
    3. PDF生成関数の正常終了
