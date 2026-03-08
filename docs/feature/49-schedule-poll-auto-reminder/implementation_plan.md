# 日程調整自動リマインド機能

## [Goal Description]
日程調整（Schedule Poll）において、設定された日時に回答していないメンバーへ自動的にDiscordでリマインダーを送信する機能を追加します。
これまで手動でのみ送信できた未回答者へのリマインドを、作成時に回答期限（deadline）を設定することで、その期限が到来した際にAzure Functionsの定期実行タスク（30分間隔）により自動で送れるようにします。

## Proposed Changes

### Backend/Database Models
- モデル `src.db.models.SchedulePoll` に `deadline` (DateTime, nullable), `reminder_sent_at` (DateTime, nullable), および `auto_reminder_stopped` (Boolean, default=False) を追加します。
- Schema `src.schemas.schedule_poll` において、`SchedulePollCreate` と `SchedulePollResponse` に `deadline: datetime | None` と `auto_reminder_stopped: bool` を追加します。
- Alembic でマイグレーションを生成して適用します。

### Backend Services & API
- API `src.api.schedule_polls` および Service `src.services.schedule_poll_service` を更新し、作成時に `deadline` を受け取ってDBに保存するようにします。
- 特定の SchedulePoll の自動リマインドをオーナー・編集者が手動で停止できるエンドポイント（例: `POST /api/projects/{project_id}/schedule_polls/{poll_id}/stop-reminder`）を追加します。
- `src.services.schedule_poll_tasks.py` を新規作成し、以下のロジックを持つ `check_poll_deadlines()` 関数を実装します：
  - `deadline` が設定されていて、かつ現在時刻が `deadline` を過ぎており、`reminder_sent_at` が None で、`is_closed` が False かつ `auto_reminder_stopped` が False である SchedulePoll を取得。
  - 各 Poll について未回答のメンバー (answers の status がないメンバー) を抽出し、Discordに送信（`remindUnansweredMembers`と同様のメッセージを自動的に構築して送信）。送信後に `reminder_sent_at` を現在時刻で更新。
- `function_app.py` に `schedule_poll_reminder` timer trigger を追加し、毎時 0分・30分 (`0 */30 * * * *`) に `check_poll_deadlines()` を呼び出します。

### Frontend
- 型情報 `frontend/src/features/schedule_polls/api/schedulePoll.ts` を更新し `deadline?: string`, `auto_reminder_stopped: boolean` やリマインド停止メソッドを追加します。
- 日程調整作成コンポーネント（一覧画面の「新しい日程調整」から呼ばれるモーダル等）に、日付および時刻の選択UIで「回答期限（任意）」を追加します。
- 詳細画面 `SchedulePollDetailPage.tsx` に回答期限の表示を追加します。
- コマンド権限（オーナー、編集者）を持つユーザーに対し、未回答メンバーのリマインドセクションに「自動リマインドを停止する」ボタンを表示し、APIを呼び出してDBフラグを更新＆UIへ反映させます。
- `frontend/src/locales/` 配下の各多言語ファイルに、`deadline` (回答期限)、`deadlineHint`、`stopAutoReminder`等のキーを追加します。

### Discord 通知の強化

#### [MODIFY] [schedule_poll_service.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/schedule_poll_service.py)
- `create_poll` メソッドにおいて、Discord通知メッセージにメンションを追加。
- メンション対象はプロジェクトの全メンバーとする（通知洩れを防ぐため）。

## Verification Plan
### Automated Tests
- バックエンドのサービスで自動リマインダー送信・停止ロジックの単体テストを拡張（余裕があれば）。
### Manual Verification
- フロントエンドで回答期限を設定した日程調整を作成できるか確認する。
- 期限を数分後に設定して作成し、手動でタイマートリガーをモック実行または待機することでDiscordに未回答者へのメンション通知が飛ぶことを確認する。
- 「自動リマインドを停止する」ボタンを押し、UI上で停止状態になったこと、及び定期実行タスクがスキップされることを確認する。
- 期限設定がない日程調整がエラーにならないことを確認する。
