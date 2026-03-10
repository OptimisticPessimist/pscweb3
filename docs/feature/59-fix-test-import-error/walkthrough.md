# [修正] テストコードのインポートエラーおよび依存関係の修正

## 修正内容

### バックエンド
- **インポートエラーの修正**: `backend/tests/integration/test_api_invitations.py`
    - `sqlalchemy.select` のインポートが漏れていたため追加しました。CIでの `NameError: name 'select' is not defined` を解決しました。
- **依存関係の追加**: `backend/pyproject.toml`
    - `email-validator` を明示的に追加しました。Pydantic V2 を使用する環境で `EmailStr` 型のバリデーションに必要となるため、インポートエラー（`ImportError: email-validator is not installed`）を回避します。

## 検証結果

### 自動テスト
- `backend` ディレクトリにて `uv run pytest tests/integration/test_api_invitations.py` を実行し、全件パスすることを確認済みです。
- ローカル環境での依存関係同期（`uv sync`）も正常に完了しています。

## 完了した作業
- [x] インポートエラーの特定と修正
- [x] 依存関係の不足解消 (`email-validator`)
- [x] ローカルでのテスト実行による検証
- [x] 修正内容の `main` ブランチへのマージとプッシュ
