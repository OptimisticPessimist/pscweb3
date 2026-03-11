# 脚本アップロード 422エラーの修正

脚本アップロード時に発生していた 422 Unprocessable Entity エラーを修正しました。

## 原因分析
フロントエンドの `apiClient` (Axios) において、デフォルトのヘッダーとして `Content-Type: application/json` が設定されていました。
これにより、`FormData` (multipart/form-data) を送信する際にも Axios が強制的に JSON として扱おうとしたり、ブラウザが自動設定するはずの `boundary` パラメータが欠落したりすることで、バックエンド（FastAPI）側でフォームデータの解析に失敗していました。

## 実施した変更

### フロントエンド
- `frontend/src/api/client.ts`: デフォルトの `Content-Type: application/json` ヘッダーを削除しました。これにより、送信データの内容（JSONかFormDataか）に応じて適切なヘッダーが自動設定されるようになります。

### バックエンド
- `backend/src/api/scripts.py`: 
    - 診断用の詳細ログ出力を削除。
    - `is_public` の型を `str` から `bool` に戻し、FastAPI の標準的なフォームバリデーションを復元。
    - 関数内での手動バリデーションを削除し、FastAPI のシグネチャによるバリデーション（`Form(...)`）を再有効化。
- `backend/src/main.py`: 
    - 診断用のエンドポイント `/api/debug/request` を削除。
    - 不要になった `Request` のインポートを削除。

## 検証結果
- フロントエンドから `FormData` を用いた脚本アップロードが正常に成功することを確認しました（バックエンド側で 422 エラーが発生しなくなりました）。
- 必須パラメータ（タイトル、ファイル）が欠落している場合に、FastAPI が適切に 422 エラーを返すことも確認しました。
