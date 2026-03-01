# タスク: 出欠リマインド送信タイミングのカスタマイズ機能

## 概要
保留状態のままのユーザーに対する「出欠確認（稽古日程）」のリマインド送信タイミングを、プロジェクトごとに「稽古時間の何時間前」として設定できるようにする。

## タスクリスト
- [ ] バックエンド: データベーススキーマの更新
  - [ ] `TheaterProject` モデルに `attendance_reminder_hours` (Integer, default=24) カラムを追加
  - [ ] Alembic マイグレーションスクリプトを作成・実行 (`alembic revision --autogenerate`, `alembic upgrade head`)
- [ ] バックエンド: APIとレスポンスの更新
  - [ ] `ProjectResponse`, `ProjectUpdate`, `ProjectCreate` スキーマに `attendance_reminder_hours` を追加
  - [ ] `src/api/projects.py` のプロジェクト作成・更新処理に `attendance_reminder_hours` を反映
- [ ] バックエンド: 定期実行タスクの更新
  - [ ] `src/services/attendance_tasks.py` 内の `check_deadlines` を修正し、`schedule_date - timedelta(hours=attendance_reminder_hours)` に基づいて一度だけリマインドを送信するロジックに変更
- [ ] フロントエンド: プロジェクト設定画面の更新
  - [ ] `src/types/index.ts` の `Project` インターフェースに `attendance_reminder_hours` を追加
  - [ ] `src/features/projects/pages/ProjectSettingsPage.tsx` のプロジェクト設定フォームにリマインド送信タイミングの入力フィールド（数値）を追加
- [ ] フロントエンド: 多言語対応 (i18n)
  - [ ] `ja`, `en`, `ko`, `zhHans`, `zhHant` の翻訳ファイルに `attendanceReminderHours` 関連のキーを追加・翻訳
- [ ] テスト・検証
  - [ ] 既存の単体テスト（リマインダー系など）が通ることを確認
  - [ ] 設定変更・リマインダー発火ロジックが期待通り動作するか手動検証
