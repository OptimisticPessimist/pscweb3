# 実装計画: CI不具合の修正 (Ruff指摘対応)

## 概要
GitHub Actions の CI で発生している Ruff のエラー（論理エラーおよび設定の問題）を修正し、CI を正常化します。

## 提案される変更

### 1. スキーマ定義の修正
- [MODIFY] [rehearsal.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/rehearsal.py)
    - `RehearsalCastCreate` の重複定義を削除し、一元化します。

### 2. ビジネスロジックの修正
- [MODIFY] [attendance.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/attendance.py)
    - 辞書内の重複キー `"style"` を削除します。

### 3. PDF生成ロジックの修正
- [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
    - ループ内で使用されていない変数 `i` を `_` に変更します。

### 4. リンター設定の調整
- [MODIFY] [pyproject.toml](file:///f:/src/PythonProject/pscweb3-1/backend/pyproject.toml)
    - `B008` (Depends指摘) を無視リストに追加（FastAPIの慣習に対応）。
    - `alembic` 配下のファイルで `E501` (行が長すぎる) を無視するように設定。

## 検証計画
### 自動テスト
- ローカルで `ruff check .` を実行し、エラーが出ないことを確認します。
- `pytest` を実行し、変更によるデグレードがないことを確認します。
