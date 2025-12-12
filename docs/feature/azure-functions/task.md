# Task List

- [x] Azure Functions 設定ファイルの作成
    - [x] `host.json` の作成
    - [x] `function_app.py` の作成
- [x] データベーススキーマの更新
    - [x] `AttendanceEvent` モデルへの `reminder_sent_at` 追加
    - [x] Alembic マイグレーションの生成と適用
- [x] Timer Function ロジックの実装
    - [x] `attendance_tasks.py` の作成（自動リマインダー処理）
    - [x] 既存の通知ロジックの統合
- [x] テストと検証
    - [x] ユニットテストの作成
    - [x] ローカル実行での動作確認
    - [ ] Azure 環境へのデプロイと確認 (次のステップ)
