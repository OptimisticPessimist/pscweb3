# タスクリスト: 脚本アップロード 422エラーの修正

- [x] 422エラーの原因調査
    - [x] バックエンドに診断ログを追加 (`backend/src/api/scripts.py`)
    - [x] 診断用エンドポイントを追加 (`backend/src/main.py`)
    - [x] フロントエンドの送信ヘッダーを確認
- [x] 修正の実施
    - [x] フロントエンドのデフォルト `Content-Type: application/json` を削除 (`frontend/src/api/client.ts`)
- [x] クリーンアップ
    - [x] バックエンドの診断ログとエンドポイントを削除
    - [x] バックエンドのフォーム型バリデーションを正常化
- [x] 検証とドキュメント作成
    - [x] アップロードの成功を確認
    - [x] `docs/feature/53-fix-script-upload-422/` にドキュメントを保存
