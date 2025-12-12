# タスクリスト

- [/] 計画
    - [x] 現状の調査
    - [x] 実装計画の作成（日本語）
    - [x] 要件の再定義（スクリプト通知の分離）
- [/] バックエンド実装
    - [x] `TheaterProject` モデルに `discord_script_webhook_url` を追加
    - [x] DBマイグレーションの生成
    - [x] `ProjectUpdate` および `ProjectResponse` スキーマの更新
    - [x] `upload_script` 処理を新Webhookに対応
- [/] フロントエンド実装
    - [x] `Project` 型定義を更新
    - [x] `ProjectSettingsPage.tsx` に入力フィールドを追加・ラベル更新
- [ ] 検証
    - [x] マイグレーション適用
    - [ ] 設定保存の動作確認
    - [ ] 通知の分離確認（スクリプト更新 vs マイルストーン作成）
