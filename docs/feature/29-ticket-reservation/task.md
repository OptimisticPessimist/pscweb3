# チケット予約システム (Ticket Reservation System) 実装タスク

## フェーズ 1: 設計・計画 (Mode: PLANNING)
- [x] 要件定義とデータベース設計の確定 (壁打ち) <!-- id: 0 -->
- [x] UI/UXデザインのすり合わせ <!-- id: 1 -->
- [x] メール送信方式の決定 <!-- id: 2 -->

## フェーズ 2: バックエンド実装 (Mode: EXECUTION)
- [x] データベースモデル作成 (`reservations` テーブル, `milestones.capacity` 追加) <!-- id: 3 -->
- [x] マイグレーションファイルの作成と適用 <!-- id: 4 -->
- [x] Pydanticスキーマの作成 (`schemas/reservation.py`) <!-- id: 4-1 -->
- [x] Emailサービス (`src/services/email.py`) の実装 (SendGrid) <!-- id: 4-2 -->
- [x] パブリック予約APIの実装 (`POST /api/public/reservations`) <!-- id: 5 -->
    - 定員チェック
    - 予約作成 (ユーザー紐付け含む)
    - 自動送信メール (BackgroundTasks)
- [x] キャスト絞り込み付き紹介者リストAPIの実装 (`GET /api/public/projects/{id}/members`) <!-- id: 5-2 -->
- [x] 予約確認APIの実装 (`GET /api/projects/{id}/reservations`) <!-- id: 6 -->
- [x] 出欠管理APIの実装 (`PATCH /api/reservations/{id}/attendance`) <!-- id: 7 -->
- [x] 予約者リストCSVエクスポートAPIの実装 (`POST /api/projects/{id}/reservations/export`) <!-- id: 8 -->
- [ ] ユニットテストの作成とパス (`tests/api/test_reservations.py`) <!-- id: 9 -->

## フェーズ 3: フロントエンド実装 (Mode: EXECUTION)
- [x] パブリック予約フォームページの実装 `TicketReservationPage.tsx` <!-- id: 10 -->
    - メールアドレス、人数、名前、紹介者選択（キャスト絞り込み機能）
- [x] 予約完了ページの作成 `ReservationCompletedPage.tsx` <!-- id: 10-1 -->
    - Googleカレンダー追加ボタン
- [x] 予約定員設定UIの実装（マイルストーン編集） `MilestoneSettings.tsx` <!-- id: 10-2 -->
- [x] 予約一覧・出欠管理ページの実装 `ReservationListPage.tsx` <!-- id: 11 -->
    - 予約者リスト表示
    - 出欠トグル
    - CSVダウンロードボタン
- [ ] 多言語対応 (i18n) <!-- id: 13 -->

## フェーズ 4: 検証・修正 (Mode: VERIFICATION)
- [ ] ローカル環境でのE2Eテスト <!-- id: 14 -->
- [ ] メール送信テスト (SendGrid) <!-- id: 15 -->
- [ ] コードレビューと修正 <!-- id: 16 -->
- [x] ドキュメント更新 (`walkthrough.md`) <!-- id: 17 -->
