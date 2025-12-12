# Discord通知チャンネル分離 実装確認

## 変更内容
- **Backend**: `TheaterProject` に `discord_script_webhook_url` を追加し、APIと通知ロジックを更新。
- **Frontend**: プロジェクト設定画面に「Script Notification Webhook URL」入力欄を追加し、ラベルを分かりやすく変更。

## 検証結果

### 1. マイグレーション
- [x] `alembic upgrade head` が正常に完了しました。

### 2. 設定画面
- [ ] 「プロジェクト設定」ページを開き、新しい項目「Script Notification Webhook URL」が表示されているか確認してください。
- [ ] 設定を保存し、再読み込みしても値が保持されているか確認してください。

### 3. 通知の分離
- [ ] **脚本通知**: 脚本をアップロード/更新し、`Script Notification Webhook URL` に設定したチャンネルに通知が届くか確認してください。
  - 未設定の場合は `General Notification Webhook URL` に届くはずです。
- [ ] **一般通知**: マイルストーンを作成し、`General Notification Webhook URL` に通知が届くか確認してください。
- [ ] **出欠確認**: 出欠確認（マイルストーン作成時のオプションなど）を行い、`Attendance Notification Channel ID` のチャンネルに通知が届くか確認してください。

## 次のステップ
- 本番環境へのデプロイ時にマイグレーションが必要です。
