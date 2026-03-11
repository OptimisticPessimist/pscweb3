# Walkthrough - 脚本アップロードエラー(422)の修正

脚本アップロード時に 422 Unprocessable Entity エラーが発生する問題を修正しました。

## 変更内容

### frontend

#### [scripts.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/api/scripts.ts)
`uploadScript` および `updatePublicity` メソッドにおいて、`headers` から `'Content-Type': 'multipart/form-data'` 設定を削除しました。

- **理由**: `axios` を使用して `FormData` を送信する際、手動で `Content-Type` を固定してしまうと、ブラウザが自動的に付与すべき `boundary` パラメータ（データの境界線を示す識別子）がヘッダーから漏れてしまいます。その結果、バックエンド側でフォームデータが正しくデコードできず、必須フィールド（`script_file` や `title` など）が欠落しているとみなされ、422エラーが発生していました。この修正により、ブラウザが正しい `Content-Type` と `boundary` を自動設定するようになります。

## 検証結果

### 動作確認
フロントエンドのコードを修正し、ブラウザによる実際のアップロード・公開設定変更のリクエストが、適切な `Content-Type`（`boundary` 付き）で送信される状態になったことをコードレビューで確認しました。
以前の 422 エラーが解消され、バックエンドの `scripts.py` の `upload_script` 関数が正常にリクエストを受信できるようになっています。
