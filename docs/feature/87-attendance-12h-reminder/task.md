# タスクリスト (12時間前リマインダー機能追加)

## 1. データベース・モデルの修正
- [ ] `backend/src/db/models.py` の修正
  - `TheaterProject` モデルに `attendance_reminder_3_hours` (default=12) を追加
  - `AttendanceEvent` モデルに `reminder_3_sent_at` を追加
- [ ] Alembicによるマイグレーションファイルの作成
  - `cd backend && pdm run alembic revision --autogenerate -m "Add reminder_3 to attendance"`
  - 自動生成されたスクリプトの内容を確認・修正
- [ ] スキーマ (`backend/src/schemas/project.py`) の更新
  - APIレスポンスに `attendance_reminder_3_hours` を含める
- [ ] データベースのマイグレーション適用 (`update_alembic.py` または `alembic upgrade head`)

## 2. バックエンド処理の修正
- [ ] `backend/src/services/attendance_tasks.py` の修正
  - `check_deadlines` に3回目のリマインダー処理を追加
  - 対象者を `status == "pending"` だけでなく、3回目の場合は `status != "ng"` (不参加以外) にする
  - `_send_reminder` の引数とメッセージ分岐を修正（12時間前用の文面を作成）

## 3. テストの修正と追加
- [ ] `backend/tests/test_attendance_tasks.py` に `reminder_3` 用のテストを追加・修正
  - 未回答(pending)と参加(ok)の対象者に12時間前リマインダーが飛ぶこと
  - 不参加(ng)の対象者には飛ばないこと
  - 全テストの実行とパス確認 (`cd backend && pdm run pytest`)

## 4. レビューと確認
- [ ] プログラムのコードレビュー
- [ ] ターミナル上で手動テストスクリプトを実行し、正常に送信されるか確認（該当データの投入などが必要なら）
- [ ] 変更内容を `walkthrough.md` に記載
- [ ] Gitへのコミットとブランチのマージ準備
