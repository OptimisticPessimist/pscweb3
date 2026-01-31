# Walkthrough - 演劇台本の書式変更

演劇台本の書式を「縦書き・横置き」に変更しました。

## Changes
### Backend

#### [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)

- PDFのページサイズを `landscape(A4)` に変更しました。これにより、縦書きのテキストが横長の用紙に配置されます。

## Validation Results
### Test Execution
`backend/test_pdf_local.py` を実行し、正常にPDFが生成されることを確認しました。
