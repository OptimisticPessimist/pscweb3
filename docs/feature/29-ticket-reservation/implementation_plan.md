# Reservation Enhancements Implementation Plan

## 目標
1.  **予約キャンセル**: ユーザーが自分で予約をキャンセルできるようにする。
2.  **Discord通知**: 予約時とキャンセル時にDiscord Webhookへ通知を送る（個人情報配慮）。
3.  **公開スケジュール**: 公開されているマイルストーン（公演）の一覧ページを作成する。

## 実装内容

### Backend (`backend/src/api/reservations.py`)
1.  **Discord通知の実装**:
    - `create_reservation` 内に `discord_service.send_notification` を追加。
    - 通知内容は指定通り（日時、名前、枚数、扱い）。メールアドレスは除外。
    - Webhook URLはプロジェクト設定 (`project.discord_webhook_url`) を使用。

2.  **キャンセルAPI (`POST /public/reservations/cancel`)**:
    - リクエスト: `reservation_id`, `email`
    - 処理: IDとEmailが一致する予約を探し、存在すれば削除（またはステータス変更、今回は削除で実装）。
    - 完了後、Discordにキャンセル通知を送信。

3.  **公開スケジュールAPI (`GET /api/public/schedule`)**:
    - 公開プロェクト (`is_public=True`) に紐づく、未来のマイルストーンを取得して返す。
    - 必要な情報: マイルストーン詳細、プロジェクト名、予約可否など。

### Frontend
1.  **公開スケジュールページ (`features/public_schedule/pages/PublicSchedulePage.tsx`)**:
    - カレンダーまたはリスト形式で公演を表示。
    - 「予約する」ボタンで `TicketReservationPage` へ遷移。
    - 既存の `ReservationListPage` とは別物（一般客用）。

2.  **予約キャンセルページ (`features/reservations/pages/ReservationCancelPage.tsx`)**:
    - 予約IDとメールアドレス入力フォーム。
    - 送信してキャンセル実行。

3.  **予約完了ページ (`ReservationCompletedPage.tsx`)**:
    - 予約IDを表示。「キャンセル時はこのIDが必要です」と案内。
    - キャンセルページへのリンクを配置。

4.  **ルーティング (`App.tsx`)**:
    - `/schedule` -> `PublicSchedulePage`
    - `/reservations/cancel` -> `ReservationCancelPage`

## 通知フォーマット
```
**🎫 チケット予約完了** (or **🗑️ チケット予約キャンセル**)
予約日時: 2025/01/01 18:00
お名前: 山田 太郎
予約枚数: 2枚
扱い: 佐藤 花子 (キャスト名など)
```

## 検証
- Webhook通知が正しく飛ぶか（ログまたは実際のDiscord）。
- キャンセルが正しく動作するか（DBから消えるか）。
- スケジュール一覧に正しいデータが表示されるか。
