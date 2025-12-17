# Azure Functions 404エラー調査計画

Azure環境において `/auth/login` エンドポイントが404エラーを返しています。ルーティング設定 (`host.json`) または `AsgiFunctionApp` の読み込みに問題がある可能性があります。

## ユーザーレビューが必要な事項
> [!NOTE]
> 問題の切り分けのため、本番環境のエントリポイント (`function_app.py`) にデバッグ用のエンドポイントを追加し、ログ出力を強化します。

## 変更内容
### Backend
#### [MODIFY] [function_app.py](file:///f:/src/PythonProject/pscweb3-1/backend/function_app.py)
- シンプルなHTTPトリガー `@app.route(route="debug")` を追加し、Function App自体が起動してリクエストを受け取れるか確認します。
- `src.main` からの `app` インポート部分を確認します。

## 検証計画
### 手動検証
- 変更をデプロイした後、ブラウザで `/api/debug` (または `/debug`) にアクセスします。
    - 成功 (200 OK) した場合: Function Appは正常に起動しており、`host.json` の設定やFastAPIとの連携部分に問題がある可能性があります。
    - 404エラーの場合: Function App自体が正しくロードされていないか、ルーティング設定が根本的に間違っている可能性があります。
- その後、再度 `/auth/login` や `/api/auth/login` へのアクセスを試みます。
