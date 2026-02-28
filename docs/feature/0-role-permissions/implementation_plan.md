# 役割別の権限調査

オーナー、編集者、閲覧者の3つの役割について、システム内でどのような操作が可能か、またどのような情報が閲覧可能かを調査します。

## Proposed Changes
- なし（調査のみ）

## Verification Plan
- バックエンドの認可ロジック（`permissions.py` および各API）の確認
- データベースモデル（`ProjectMember`）の確認
