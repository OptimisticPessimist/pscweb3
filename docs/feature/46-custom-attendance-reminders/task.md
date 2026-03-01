# タスク: 出欠リマインド送信タイミングのカスタマイズ機能

## 概要
保留状態のままのユーザーに対する「出欠確認（稽古日程）」のリマインド送信タイミングを、プロジェクトごとに「1回目のリマインド（稽古時間の何時間前）」「2回目のリマインド（稽古時間の何時間前）」として設定できるようにする。

## タスクリスト
- [x] バックエンド: データベーススキーマの更新
  - [x] `TheaterProject` モデルの `attendance_deadline_reminder_hours` 等を `attendance_reminder_1_hours`, `attendance_reminder_2_hours` に変更
  - [x] Alembic マイグレーションスクリプトを作成・実行 (`alembic revision --autogenerate`, `alembic upgrade head`)
- [x] バックエンド: APIとレスポンスの更新
  - [x] `ProjectResponse`, `ProjectUpdate`, `ProjectCreate` スキーマのカラムを追加・変更
  - [x] `src/api/projects.py` のプロジェクト作成・更新処理にカラムを反映
- [x] バックエンド: 定期実行タスクの更新
  - [x] `AttendanceEvent` モデルのリマインダー履歴フラグを `reminder_1_sent_at`, `reminder_2_sent_at` に変更
  - [x] Alembic マイグレーションスクリプトを作成・実行
  - [x] `src/services/attendance_tasks.py` 内の `check_deadlines` を2つのイベント（「1回目」「2回目」）として処理するロジックに変更
- [x] フロントエンド: プロジェクト設定画面の更新
  - [x] `src/types/index.ts` の `Project` インターフェースのカラム名を変更
  - [x] `src/features/projects/pages/ProjectSettingsPage.tsx` のプロジェクト設定フォームに、それぞれの数値を入力できるフィールドを追加
- [x] フロントエンド: 多言語対応 (i18n)
  - [x] `ja`, `en`, `ko`, `zhHans`, `zhHant` の翻訳ファイルに `attendanceReminder1Hours` / `attendanceReminder2Hours` 関連のキーを追加・翻訳
- [x] テスト・検証
  - [x] 既存の単体テスト（リマインダー系など）が通ることを確認
  - [x] 設定変更・リマインダー発火ロジックが期待通り動作するか手動検証
