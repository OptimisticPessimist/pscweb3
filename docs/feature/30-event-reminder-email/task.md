# チケット予約当日通知メール機能

## 概要
チケット予約者に対して、公演当日に自動でリマインダーメールを送信する機能を実装。

## タスクリスト

### バックエンド実装
- [x] Email Service拡張
    - [x] `send_event_reminder`メソッド追加（当日通知メール送信）
- [x] タスクサービス追加
    - [x] `reservation_tasks.py`を作成（定期実行タスク処理）
    - [x] 当日のReservationをチェックして通知メールを送信する関数
- [x] エンドポイント追加（手動トリガー用・オプション）
    - [x] `POST /api/admin/tasks/send-event-reminders` エンドポイント（手動実行用）

### 定期実行設定
- [ ] Azure Functions Timer Triggerの設定方法を文書化
    - [ ] `function.json`設定例の追加
    - [ ] ローカル開発での実行方法

### テスト
- [x] ユニットテスト追加
    - [x] `send_event_reminder`のテスト
    - [x] `check_upcoming_events`タスクのテスト
- [x] 統合テスト
    - [x] 当日のReservationに対してメールが送信されるか確認

### ドキュメント
- [ ] `docs/feature/30-event-reminder-email/`にドキュメント保存
    - [ ] `task.md`
    - [ ] `implementation_plan.md`
    - [ ] `walkthrough.md`

### 検証
- [ ] ローカルで手動実行してメール送信を確認
- [ ] TimerTriggerの動作を確認（モック時刻で）
