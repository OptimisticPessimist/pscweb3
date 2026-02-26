# 日程調整未回答メンバーのリマインド機能

日程調整において未回答のメンバーを把握し、Discordでメンション付きのリマインドを送る機能を実装します。特定のメンバーを通知対象から除外できる選択機能も含めます。

## User Review Required
特になし。

## Proposed Changes

### Backend

#### [MODIFY] src/schemas/schedule_poll.py
新規スキーマを追加します。
- `UnansweredMemberResponse`: 未回答メンバー情報（`user_id`, `name`, `role`, `discord_id` 等）
- `RemindUnansweredRequest`: リマインド送信リクエスト（`target_user_ids`: 送信対象のユーザーIDのリスト）

#### [MODIFY] src/services/schedule_poll_service.py
新規メソッドを追加します。
- `get_unanswered_members(poll_id)`
  - 対象の `SchedulePoll` のすべての回答から回答済みユーザーIDセットを取得。
  - プロジェクトの全メンバーから回答済みユーザーを除外し、未回答メンバーリストとして返却。メンバーの役職情報も結合する。
- `send_reminder(poll_id, target_user_ids)`
  - 指定された `target_user_ids` に該当する `User` の `discord_id` を取得。
  - プロジェクトのDiscordチャンネル（またはWebhook URL）に対して、特定のユーザーをメンション（`<@discord_id>`）するリマインドメッセージを送信。
  - メッセージには日程調整のタイトルとWebフォームへのリンクを含める。

#### [MODIFY] src/api/schedule_polls.py
以下の2つのAPIエンドポイントを追加します。
- `GET /projects/{project_id}/polls/{poll_id}/unanswered` : 未回答メンバーリストを取得
- `POST /projects/{project_id}/polls/{poll_id}/remind` : 選択されたターゲットにリマインド送信実行

### Frontend

#### [MODIFY] src/features/schedule_polls/api/schedulePoll.ts
新規APIコールの定義を追加します。
- `getUnansweredMembers(projectId, pollId)`
- `remindUnansweredMembers(projectId, pollId, targetUserIds)`

#### [MODIFY] src/features/schedule_polls/components/...
「未回答メンバー」セクションを追加します。
- APIから未回答メンバー一覧を取得して表示。
- 各メンバーの横にチェックボックスを配置し、デフォルトでチェック状態（ON/OFFでリマインド対象から除外可能）にする。
- 「リマインドを送信」ボタンを設置し、押下時にチェックされたメンバーID群をPOST送信する。

## Verification Plan

### Automated Tests
- `pytest backend/tests/unit/test_schedule_poll_service.py` などで新規追加する `get_unanswered_members` やコマンドが正しく動作するかテストを追加・実行。

### Manual Verification
1. ローカル環境で立ち上げた画面を開き、日程調整の詳細ページへアクセス。
2. 一部のメンバーで回答し、未回答メンバー一覧がただしく表示されるか確認。
3. 任意のメンバーのチェックを外し、「リマインドを送信」ボタンをクリック。
4. 対象メンバーのみがDiscord上で通知・メンションされることを確認する。
