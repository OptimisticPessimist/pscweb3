# 実装計画: 出欠確認の12時間前リマインダー (出席予定者向け)

目的: 出欠確認に回答したかしていないかに関わらず、欠席を確認している出席予定者（`status == "ng"`）**以外**の出席予定者に対して、スケジュールの12時間前にリマインドメッセージを送信する機能を追加する。現状は未実装（未回答者への48時間前・24時間前リマインダーのみ実装済み）であるため、新規の「3回目のリマインダー」として追加機能として実装する。

## ユーザーレビュー必須の項目
> [!NOTE]
> 現在のシステムでは、未回答者（pending）に対して1回目（デフォルト48時間前）、2回目（デフォルト24時間前）のリマインダーを行っています。「12時間前のリマインダー」について、各プロジェクトの管理者が時間（12時間）を変更できるように `TheaterProject` テーブルに `attendance_reminder_3_hours` というカラムを追加します。固定で12時間にしたい場合はご指示ください。今回は柔軟性を持たせるためカラムを追加する想定で進めます。

## 提案する変更

### Database Models & Migrations
1. `TheaterProject` モデルに `attendance_reminder_3_hours` (Integer, default=12) を追加。
2. `AttendanceEvent` モデルに `reminder_3_sent_at` (DateTime, nullable=True) を追加。
3. Alembicでマイグレーションスクリプトを作成・実行する。

#### [MODIFY] models.py(file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
#### [MODIFY] project.py(file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/project.py)

---

### Backend Services
`attendance_tasks.py` の定時実行タスク `check_deadlines` において、3回目のリマインダー送信処理を追加する。

- 既存の処理では `pending` (未回答) なターゲットのみを抽出して1回目・2回目のリマインダーを送信している。
- **変更後**: 対象ターゲットを分ける。
  - 1・2回目用: `status == "pending"`
  - 3回目用: `status != "ng"` (すなわち `ok` と `pending` の両方が対象)
- `_send_reminder` メソッドを拡張し、`reminder_type == "3"` の場合は、以下のような文面にする。
  - 「**【自動リマインダー】間もなく稽古(12時間前)です。出席予定の方は忘れずにご参加ください。未回答の方は至急出欠を入力してください。**」

#### [MODIFY] attendance_tasks.py(file:///f:/src/PythonProject/pscweb3-1/backend/src/services/attendance_tasks.py)

---

### Tests
新規のロジックが正しく動くか、及び既存の動作（1回目、2回目）が壊れていないかを確認するために単体テストを更新・追加する。

#### [MODIFY] test_attendance_tasks.py(file:///f:/src/PythonProject/pscweb3-1/backend/tests/test_attendance_tasks.py)

## 検証計画

### 自動テスト
- `cd backend && pdm run pytest tests/test_attendance_tasks.py -v` を実行し、以下のシナリオを全てPassすることを確認する。
  1. `pending` と `ok` のユーザーには3回目のリマインダーが送信され、`ng` のユーザーには送信されないこと。
  2. 1回目、2回目のリマインダーは引き続き `pending` のユーザーのみに送信されること。

### 手動検証
- テストスクリプト等を用いて、DB上に12時間前を切った `AttendanceEvent`（`status` を色々と混ぜた `AttendanceTarget`）を用意し、実際に `check_deadlines()` を手動トリガーしてDiscordに想定通りのメンションが飛ぶか確認する。
