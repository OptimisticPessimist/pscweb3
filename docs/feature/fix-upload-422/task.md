# タスク: 脚本アップロードエラー(422)の修正

## ステータス
- [x] 原因の調査と特定
  - [x] バックエンド `scripts.py` の確認
  - [x] フロントエンド `scripts.ts` の `Content-Type` 設定の確認
- [x] 修正の実施
  - [x] `frontend/src/features/scripts/api/scripts.ts` の修正
- [x] 動作確認
  - [x] アップロードの正常終了を確認
- [x] ドキュメント作成とマージ
  - [x] `walkthrough.md` の作成
  - [x] ブランチのマージ（ `feature/fix-upload-422` ）
