# Notify Unanswered Members (未回答メンバーリマインド機能)

## 概要
日程調整（Schedule Poll）において、まだ回答を提出していないメンバーを抽出し、一括してDiscord上でリマインドメンション付きの通知を送る機能を実装しました。また、指定したメンバーのみを選択してリマインドを送る（特定のメンバーを除外する）ことも可能です。

## 変更内容

### 1. バックエンド
*   **未回答メンバー取得API**: `GET /api/v1/projects/{project_id}/polls/{poll_id}/unanswered`
    *   プロジェクトの全メンバーと、現在の日程調整の各候補日に回答済みのメンバーを比較し、まだ一つも回答していないメンバーのリストを返します。
*   **リマインド送信API**: `POST /api/v1/projects/{project_id}/polls/{poll_id}/remind`
    *   フロントエンドから送信された対象メンバーのIDリスト（`target_user_ids`）を受け取り、DiscordのWebhookまたはチャンネルに対して、対象者へのメンションを含むリマインドメッセージを送信します。
*   **スキーマの追加**:
    *   `UnansweredMemberResponse`
    *   `RemindUnansweredRequest`
*   **サービスの追加**:
    *   `SchedulePollService.get_unanswered_members`
    *   `SchedulePollService.send_reminder`

### 2. フロントエンド
*   **未回答メンバー一覧の表示**:
    *   日程調整詳細画面 (`SchedulePollDetailPage.tsx`) 内の、回答グリッドの下に「未回答メンバーのリマインド」セクションを追加しました。
    *   APIから取得した未回答のメンバーの名前を一覧で表示します。
*   **送信対象の選択機能**:
    *   各メンバーの表示部分はトグル（チェックボックス）になっており、クリックすることでリマインド送信対象から除外・追加が素早く行えます（デフォルトは全員選択）。
*   **リマインド実行のUI**:
    *   選択されたメンバー人数をボタンに表示し（例：「N名にリマインドを送信」）、クリックすることでAPIへリマインドリクエストを送信します。
*   **APIクライアントの拡張**:
    *   `schedulePollApi.ts` に、`getUnansweredMembers` と `remindUnansweredMembers` のメソッドを追加しました。

### 3. テストと検証
*   **自動テスト**:
    *   `test_schedule_poll_service.py` 内に、`get_unanswered_members` と `send_reminder` に関する新しいユニットテストを追加しました。正常に動作し、テストがパスすることを確認済みです。
*   **UI構文エラーの修正**:
    *   実装中に発生した `SchedulePollDetailPage.tsx` での `div` タグの閉じ忘れによる構文エラーを修正し、Lintエラーが解消された状態であることを確認しました。

以上で、本機能の実装を完了します。
