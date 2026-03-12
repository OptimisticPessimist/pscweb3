# 実装計画 - Ruffインポート順序の修正

Ruffのリンターによって指摘されたインポート順序の不備を修正します。

## 1. 現状の課題
- `src/services/pdf_generator.py` において、インポートブロックが適切にソートまたはフォーマットされていない (`I001`)。
- `src/utils/fountain_utils.py` において、インポートブロックの形式に不備がある (`I001`)。

## 2. 修正方針
- `ruff check --select I --fix` を使用して、自動的にインポート順序を修正する。
- 修正後、再度 `ruff check` を実行してエラーが解消されたことを確認する。

## 3. 確認方法
- `ruff check --select I` を実行し、「All checks passed!」と表示されることを確認する。
