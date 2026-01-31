# [演劇台本の書式変更]

演劇台本の一般的な書式である「縦書きで紙は横置き」に対応するため、PDF生成時の用紙設定を変更する。

## User Review Required
特になし

## Proposed Changes
### Backend
#### [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
- `pdf_generator.py`を修正
    - メタデータから `synopsis` または `あらすじ` を取得する処理を追加
    - メタデータの挿入先を `TITLE` 行から `AUTHOR` 行に変更する
        - `TITLE` 行の書式（太文字・中央揃え等を想定）を維持するため
        - `AUTHOR` 行が存在しない場合は新規作成して `TITLE` の後に挿入する
    - メタデータの表示順序を調整（Author, Synopsis, Date... の順など）

## Verification Plan
### Automated Tests
- `backend/test_pdf_local.py` を実行し、エラーなくPDFが生成されることを確認する。
- 生成されたPDFのファイルサイズが変更されていることを確認する（用紙サイズ変更による）。

### Manual Verification
- 生成されたPDFを開き、用紙が横向きで、テキストが縦書きになっていることを確認する（※今回は環境上閲覧不可のため、コード設定値と実行ログで判断）。
