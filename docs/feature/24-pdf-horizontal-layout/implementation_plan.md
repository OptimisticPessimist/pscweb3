# [演劇台本の書式変更]

演劇台本の一般的な書式である「縦書きで紙は横置き」に対応するため、PDF生成時の用紙設定を変更する。

## User Review Required
特になし

## Proposed Changes
### Backend
#### [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
- `reportlab` から `landscape`, `A4` をインポート
- `psc_to_pdf` の呼び出し時に `size=landscape(A4)` を指定するように変更

## Verification Plan
### Automated Tests
- `backend/test_pdf_local.py` を実行し、エラーなくPDFが生成されることを確認する。
- 生成されたPDFのファイルサイズが変更されていることを確認する（用紙サイズ変更による）。

### Manual Verification
- 生成されたPDFを開き、用紙が横向きで、テキストが縦書きになっていることを確認する（※今回は環境上閲覧不可のため、コード設定値と実行ログで判断）。
