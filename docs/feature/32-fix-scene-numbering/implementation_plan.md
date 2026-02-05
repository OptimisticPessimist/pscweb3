# CI修正の実装計画

## 問題の説明
直近の変更後、ユニットテストと統合テストで複数のCI失敗が発生しました。
1. `reservation_tasks.py` で `NameError: name 'AsyncSession' is not defined` が発生。
2. `test_api_castings.py` で `TypeError: list indices must be integers` が発生。
3. `test_api_projects.py` および `test_api_invitations.py` で 401 Unauthorized エラーが発生。
4. `test_api_invitations.py` で 404 Not Found エラーが発生。
5. `test_project_limit.py` で 400 Bad Request（上限エラー）が発生。
6. `test_synopsis_logic.py` でアサーションエラー（シーン数不一致）が発生。

## 変更提案

### 1. [reservation_tasks.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/reservation_tasks.py) のインポート漏れ修正
- `sqlalchemy.ext.asyncio` から `AsyncSession` をインポートします。

### 2. 統合テストの認証ヘッダー修正
- **対象ファイル**:
    - [test_api_projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/integration/test_api_projects.py)
    - [test_api_invitations.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/integration/test_api_invitations.py)
- **変更内容**: `params={"token": token}` を `headers={"Authorization": f"Bearer {token}"}` に置き換えます。

### 3. キャスティングレスポンス処理の修正
- **対象ファイル**: [test_api_castings.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/integration/test_api_castings.py)
- **変更内容**: APIはキャスティングのリストを返します。辞書としてのアクセスではなく、リスト内の項目に適切にアクセスするようにアサーションを修正します。

### 4. プロジェクト作成上限テストの修正
- **対象ファイル**: [test_project_limit.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/unit/test_project_limit.py)
- **変更内容**: テスト実行前にユーザーの状態をクリーンにする（非公開プロジェクト数0）か、このテスト専用の新規ユーザーを作成して競合を回避します。

### 5. あらすじロジックテストの修正
- **対象ファイル**: [test_synopsis_logic.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/unit/test_synopsis_logic.py)
- **変更内容**: シーン数が3ではなく2になっている原因を調査します。シーン結合の影響を受けている可能性がありますが、あらすじ（Scene 0）は通常結合されないはずです。ロジックを確認し、必要であればテストまたは実装を修正します。

## 検証計画
- 影響を受けるファイルの `pytest` を実行します。
- ローカルでフルテストスイートを実行し、全テストパスを確認します。
