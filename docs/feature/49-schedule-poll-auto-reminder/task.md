# タスク: 日程調整の自動リマインド機能実装

- [x] Backend: `SchedulePoll` モデルに `deadline` と `reminder_sent_at` を追加
- [x] Backend: `SchedulePoll` モデルに `auto_reminder_stopped` を追加
- [x] Backend: DBマイグレーションの実行
- [x] Backend: Pydanticスキーマ (`SchedulePollCreate`, `SchedulePollResponse`) の更新
- [x] Backend: `SchedulePollService` に `check_poll_deadlines` と `stop_auto_reminder` を実装
- [x] Backend: `backend/src/api/schedule_polls.py` に `stop-reminder` エンドポイントを追加
- [x] Backend: `function_app.py` にタイマートリガーを登録
- [x] Frontend: APIクライアント (`schedulePoll.ts`) の更新
- [x] Frontend: `SchedulePollCreatePage.tsx` に回答期限入力フィールドを追加
- [x] Frontend: `SchedulePollDetailPage.tsx` に回答期限表示と自動リマインド停止ボタンを追加
- [x] Frontend: 多言語対応 (ja, en, ko, zh-Hans, zh-Hant) の更新
- [x] Backend: 日程調整作成時のDiscord通知にメンションを追加
- [x] [Walkthrough](file:///f:/src/Project/pscweb3-1/docs/feature/49-schedule-poll-auto-reminder/walkthrough.md) の更新
