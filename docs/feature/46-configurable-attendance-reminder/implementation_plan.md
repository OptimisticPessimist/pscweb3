# 実装計画: 出欠リマインド時間のカスタマイズ対応

ユーザーが保留状態のメンバーへ出欠リマインドを送るタイミングを、「稽古（イベント）時間の何時間前か」で設定できるようにします。
これはプロジェクト単位の設定として実装します。

## Proposed Changes

### データベースモデルとマイグレーション
- **[MODIFY]** `backend/src/db/models.py`
  - `TheaterProject` に `attendance_reminder_hours: Mapped[int] = mapped_column(default=24)` を追加します。
- **[NEW]** `backend/alembic/versions/` 以下
  - 新しいカラムのマイグレーションスクリプトを作成します。

### バックエンドAPI
- **[MODIFY]** `backend/src/schemas/project.py`
  - `ProjectResponse`, `ProjectUpdate`, `ProjectCreate` スキーマに `attendance_reminder_hours` (int | None) を追加します。
- **[MODIFY]** `backend/src/api/projects.py`
  - `create_project`, `update_project`, `_build_project_response` 等で `attendance_reminder_hours` を保存・返却できるようにします。

### バックエンドの定期処理（リマインダータスク）
- **[MODIFY]** `backend/src/services/attendance_tasks.py`
  - `check_deadlines` メソッドを修正し、対象イベントの抽出条件を変更します。
  - 現在時刻が `schedule_date` の `attendance_reminder_hours` 時間前を過ぎた時点でリマインダーをトリガーするようにします。
  - （イベントに `schedule_date` が設定されていない場合は従来の `deadline` 基準を残します）。

### フロントエンド（UIと通信部分）
- **[MODIFY]** `frontend/src/types/index.ts`
  - `Project` 型に `attendance_reminder_hours: number` を追加します。
- **[MODIFY]** `frontend/src/features/projects/pages/ProjectSettingsPage.tsx`
  - `ProjectUpdateForm` コンポーネントに、「出欠リマインド送信タイミング（イベントの〇〇時間前）」の数値入力欄を追加します。
- **[MODIFY]** `frontend/src/locales/*/translation.json` (ja, en, ko, zhHans, zhHant)
  - 全5言語に対して設定項目用の文言を追加します。

## Verification Plan

### Automated Tests
- バックエンドのテストコマンド `pytest backend/tests/unit/test_attendance_tasks.py` 等を実行し、リマインダー送信ロジックが既存の機能を壊していないか確認します。
- 新しい日時判定ロジックに対して、テスト（`test_check_deadlines`等）を修正・拡張します。

### Manual Verification
1. フロントエンドからプロジェクト設定を開き、「出欠リマインド送信タイミング」に任意の数値（例: 2時間前）を入力して保存できることを確認します。
2. そのプロジェクトでマイルストーンを作成し、出欠イベントを生成します（日時は未来で設定）。
3. 手動で出欠イベントの時間を操作するか、モック時間を使用して `check_deadlines` を実行し、設定した「2時間前」のタイミングでDiscordのチャンネルにリマインド通知が飛ぶことを確認します。
