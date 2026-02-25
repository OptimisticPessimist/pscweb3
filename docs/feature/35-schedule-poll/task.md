# グループスケジュール調整機能 (日程調整機能) 実装タスク

## 要件の深堀りと既存機能の確認 (Planning)
- [x] 既存のDBモデル (`db/models.py`) の確認 (スケジュール、出欠、プロジェクト関連)
- [x] Discord連携の既存実装 (`services/discord.py`) の確認
- [x] 既存のスケジュールAPI (`api/rehearsals.py`, `api/attendance.py`, `api/reservations.py` など) の確認
- [x] 日程調整機能に対するアーキテクチャ・DBスキーマの検討
- [x] Discord BOTを使った日程調整入力フローの設計
- [x] 実装計画 (`implementation_plan.md`) の作成とユーザーレビュー

## 実装作業 (Execution)
- [x] 日程調整用のDBモデル作成/拡張 (`db/models.py`)
- [x] マイグレーションスクリプトの生成 (`alembic revision --autogenerate`)
- [x] バックエンド: 日程調整のCRUD API作成 (`schemas/schedule_poll.py`, `api/schedule_polls.py`)
- [x] バックエンド: Discordインタラクションエンドポイントの機能追加 (`api/interactions.py`)
- [x] バックエンド: ビジネスロジック・コンポーネント生成処理 (`services/schedule_poll_service.py`)
- [x] バックエンド: 既存のスケジュール機能（稽古予定等）への連携処理作成 (`api/schedule_polls.py` の `finalize` エンドポイント)
- [ ] （必要であれば）フロントエンド: 日程調整一覧・作成・回答画面の作成 (Web UIは必要だが、バックエンド・Discord連携を優先して完了)
- [x] ユニットテスト/インテグレーションテストの作成

## 検証 (Verification)
- [x] 自動テストの実行・パスの確認
- [ ] Discordを利用した手動動作確認 (環境があれば)
- [x] `walkthrough.md` の作成、検証結果の記述
- [x] コードレビューの実施
