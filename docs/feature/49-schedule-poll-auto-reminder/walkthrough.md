# Walkthrough: 日程調整の自動リマインド機能

日程調整機能において、回答期限を設けて未回答者に自動でリマインドを送る機能、およびその自動リマインドをオーナーや編集者が手動で停止できる機能を実装しました。

## 実施内容

### 1. データベースとモデルの更新
- `SchedulePoll` モデルに以下のフィールドを追加しました。
  - `deadline`: 回答期限（UTC保存）
  - `reminder_sent_at`: 最後に自動リマインドを送信した時刻
  - `auto_reminder_stopped`: 自動リマインドが手動で停止されたかどうかのフラグ
- Alembic を使用してデータベースのスキーマを更新しました。

### 2. バックエンドロジックの実装
- `SchedulePollService` に以下のメソッドを追加・更新しました。
  - `create_poll`: 作成時に `deadline` を受け取るように拡張。
  - `check_poll_deadlines`: 30分ごとに実行され、期限を過ぎてリマインド未送信の投票を探して Discord 通知を送るロジック。
  - `stop_auto_reminder`: 自動リマインドを停止するフラグをセットするロジック。
- FastAPI 共通 API に `/stop-reminder` エンドポイントを追加し、権限チェック（Editor以上）を実装しました。

### 3. バックグラウンドタスクの登録
- `backend/function_app.py` に `schedule_poll_reminder` タイマートリガーを登録し、30分ごとに自動チェックが走るように設定しました。

### 4. フロントエンドの更新
- **作成画面**: 任意で回答期限（日付と時刻）を設定できる入力フィールドを追加しました。
- **詳細画面**: 
  - ヘッダー部分に回答期限を表示するようにしました。
  - リマインドセクションに、権限を持つユーザー向けに「自動リマインド停止」ボタンを追加しました。
- **API クライアント**: `stopAutoReminder` メソッドの追加と型定義の更新を行いました。

### 5. 多言語対応
- 以下のすべての言語で、新しい機能に関連する文字列を追加しました。
  - 日本語 (ja)
  - 英語 (en)
  - 韓国語 (ko)
  - 簡体字中国語 (zh-Hans)
  - 繁体字中国語 (zh-Hant)

## 検証結果

### 自動リマインドの挙動
- `SchedulePollService.check_poll_deadlines` のロジックにおいて、以下の条件でリマインドが送信されることを確認：
  - `deadline` が現在時刻より前
  - `reminder_sent_at` が NULL
  - `auto_reminder_stopped` が FALSE
  - 未回答のメンバーが存在する

### 手動停止機能の挙動
- `/stop-reminder` API を呼ぶことで `auto_reminder_stopped` が TRUE になり、その後の `check_poll_deadlines` でスキップされることを確認。
- フロントエンド詳細画面で、停止後は「自動リマインド停止済み」と表示されることを確認。
