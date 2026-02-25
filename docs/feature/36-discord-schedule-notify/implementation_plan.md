# 実装計画: Discordへのスケジュール通知追加 (機能: 36-discord-schedule-notify)

## 目的
日程調整APIによる「スケジュール確定時」と、稽古スケジュールAPIによる「スケジュール更新時」に、対象プロジェクトのDiscord Webhookへ通知メッセージを送信する機能を追加する。現在、スケジュールの追加時および削除時には通知が実装されているが、確定時と更新時には通知が実装されていないため、これを補完する。

## ユーザーへの確認事項 (User Review Required)
- **メンションの対象について**:
  - `update_rehearsal` では、稽古の参加者(participants)およびキャスト(casts)として割り当てられているユーザー全員にメンションを飛ばす想定です（追加・削除時と同様）。
  - `finalize_poll` (日程調整からの確定) では、現状のコードではキャストや参加者の自動割り当て関数が未実装 (`#TODO: キャスト・参加者の自動登録ロジック`) となっています。そのため、ここではメンションを付けずに「📅 日程調整の結果、以下の稽古スケジュールが確定しました」という全体通知のみを送信する形で進めてよいでしょうか？

## 変更内容提案 (Proposed Changes)

### `backend/src/api/schedule_polls.py`
#### [MODIFY] `schedule_polls.py`(file:///f:/src/PythonProject/pscweb3-1/backend/src/api/schedule_polls.py)
- **`finalize_poll` 関数の引数追加**:
  - `discord_service: DiscordService = Depends(get_discord_service)` を追加。
  - `background_tasks: BackgroundTasks` を追加。
- **通知処理の追加**:
  - スケジュール (`Rehearsal`) の作成・保存完了直後に、`project = await db.get(TheaterProject, project_id)` を用いてプロジェクト情報を取得。
  - `project.discord_webhook_url` が設定されている場合、日時 (`rehearsal.date`) および場所などの情報をフォーマットし、「📅 **日程調整の結果、稽古が確定しました**」という文面で `discord_service.send_notification` をバックグラウンドタスクとして呼び出す。

### `backend/src/api/rehearsals.py`
#### [MODIFY] `rehearsals.py`(file:///f:/src/PythonProject/pscweb3-1/backend/src/api/rehearsals.py)
- **`update_rehearsal` 関数の引数追加**:
  - `discord_service: DiscordService = Depends(get_discord_service)` を追加。
  - `background_tasks: BackgroundTasks` を追加。
- **通知処理の追加**:
  - データの更新処理およびコミット (`await db.commit()`) の完了後に通知処理を挿入。
  - スケジュールの紐づく `TheaterProject` を取得。
  - 退避・取得した関係者（`participants`, `casts`）の `user.discord_id` をリストアップし、メンション文字列を構築。
  - `project.discord_webhook_url` が存在する場合、「📝 **稽古スケジュールが更新されました**」という文面で通知メッセージを生成し、`discord_service.send_notification` をバックグラウンド処理に追加。

## 検証計画 (Verification Plan)

### 手動検証 (Manual Verification)
1. ローカルバックエンドサーバー（`uv run uvicorn src.main:app --reload`）が起動している状態で、Swagger UI (`http://localhost:8000/docs`) またはフロントエンド画面を開く。
2. 対象プロジェクト（Discord Webhook設定済み）にて、登録されている「日程調整(Poll)」を**確定(finalize)**し、Discord（またはモックコンソール）に「日程調整の結果、稽古が確定しました」のメッセージが到達するか確認する。
3. 既存の稽古スケジュールを**更新(update)**（例えば場所の変更やキャストの追加・削除を実行）し、Discordに「稽古スケジュールが更新されました」というメッセージとともに対象者へのメンションが送られるか確認する。

### 自動テスト検証 (Automated Tests)
- `pytest backend/tests/` 系のテストスイートを実行し、依存注入（`Depends`）の変更によるAPIエラーやリグレッションが発生していないか確認する。
