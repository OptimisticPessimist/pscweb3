# 実装計画: 出欠リマインド時間のカスタマイズ対応

ユーザーが保留状態のメンバーへ出欠リマインドを送るタイミングを以下の2つ設定できるようにします。
これはプロジェクト単位の設定として実装します。
1. **1回目のリマインド: 稽古日時の何時間前か** (`attendance_reminder_1_hours`)
2. **2回目のリマインド: 稽古日時の何時間前か** (`attendance_reminder_2_hours`)

## Proposed Changes

### データベースモデルとマイグレーション
- **[MODIFY]** `backend/src/db/models.py`
  - `TheaterProject` に `attendance_reminder_1_hours: Mapped[int] = mapped_column(default=48)` を追加・変更します。
  - `TheaterProject` に `attendance_reminder_2_hours: Mapped[int] = mapped_column(default=24)` を追加・変更します。
  - `AttendanceEvent` の `schedule_reminder_sent_at` 等を `reminder_1_sent_at` と `reminder_2_sent_at` に変更します。
- **[NEW]** `backend/alembic/versions/` 以下
  - 新しいカラムの追加や変更に関するマイグレーションスクリプトを作成します。

### バックエンドAPI
- **[MODIFY]** `backend/src/schemas/project.py`
  - `ProjectResponse`, `ProjectUpdate`, `ProjectCreate` スキーマに2つのカラム (int | None) を追加します。
- **[MODIFY]** `backend/src/api/projects.py`
  - `create_project`, `update_project`, `_build_project_response` 等で新しい2つのカラムを処理します。

### バックエンドの定期処理（リマインダータスク）
- **[MODIFY]** `backend/src/services/attendance_tasks.py`
  - `check_deadlines` メソッドを改修し、以下の2種類の対象イベントを抽出・処理します。
    1. 現在時刻が `schedule_date` の `attendance_reminder_1_hours` 時間前を過ぎており、まだ `reminder_1_sent_at` が記録されていないもの。
    2. 現在時刻が `schedule_date` の `attendance_reminder_2_hours` 時間前を過ぎており、まだ `reminder_2_sent_at` が記録されていないもの。
  - 送信メッセージも、どちらのリマインダーかに応じて件名や本文を微調整します。

### フロントエンド（UIと通信部分）
- **[MODIFY]** `frontend/src/types/index.ts`
  - `Project` 型に2つのカラムを追加します。
- **[MODIFY]** `frontend/src/features/projects/pages/ProjectSettingsPage.tsx`
  - `ProjectUpdateForm` コンポーネントに、「1回目の出欠リマインド（稽古の〇〇時間前）」「2回目の出欠リマインド（稽古の〇〇時間前）」の数値入力欄を追加・修正します。
- **[MODIFY]** `frontend/src/locales/*/translation.json` (ja, en, ko, zhHans, zhHant)
  - 全5言語に対してそれぞれの設定項目用の文言を追加します。

## Verification Plan

### Automated Tests
- `pytest backend/tests/unit/test_attendance_tasks.py` 等を実行し、リマインダーの送出ロジックが期待通りに2回動作するか、既存の機能を壊していないか確認します。
- 複数カラムのステータス更新判定を中心にテストを拡充します。

### Manual Verification
1. フロントエンドのプロジェクト設定項目が2つ表示され、それぞれ保存・読込ができることを確認します。
2. モック時間を使用して、または適切な未来時間を設定した上で、それぞれの時間を過ぎた時点で2回Discord通知が飛ぶことを確認します。
