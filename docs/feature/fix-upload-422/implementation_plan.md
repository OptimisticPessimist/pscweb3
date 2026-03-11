# 実装計画 - 脚本アップロードエラー(422)の修正

脚本アップロード時に 422 Unprocessable Entity エラーが発生する問題を修正します。

## ユーザーレビューが必要な項目
- ありません。

## Proposed Changes

### frontend

#### [MODIFY] [scripts.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/api/scripts.ts)
- `uploadScript` および `updatePublicity` メソッドにおいて、`headers` から `'Content-Type': 'multipart/form-data'` を削除します。
  - **理由**: `axios` で `FormData` を送信する場合、手動で `Content-Type` を設定すると、ブラウザが自動付与する `boundary` パラメータが欠落し、バックエンドがマルチパートデータを正しく解析できなくなります（結果として必須フィールドが欠落しているとみなされ 422 エラーとなります）。

### backend (Optional/Cleanup)

#### [MODIFY] [scripts.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/scripts.py)
- コード内のコメントや不要な型変換があれば整理します。

## Verification Plan

### Automated Tests
- フロントエンドの問題であるため、ブラウザを使用してアップロード機能の正常動作を確認します。
- 必要に応じて、`curl` などでマルチパートリクエストを手動送信し、バックエンドが正しく受け取れるか検証します。

### Manual Verification
1.  プロジェクトの脚本一覧ページから「アップロード」ボタンをクリックします。
2.  適当な `.fountain` ファイルを選択し、タイトル等を入力して「アップロード」を実行します。
3.  エラーなくスクリプト一覧に戻り、新しいスクリプトが表示されることを確認します。
