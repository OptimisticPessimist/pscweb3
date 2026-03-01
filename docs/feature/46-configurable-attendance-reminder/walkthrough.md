# 実装完了: 出欠リマインド時間のカスタマイズ対応

ユーザーが保留状態のメンバーへ出欠リマインドを送るタイミングを以下の2つ設定できるようにする機能の実装がすべて完了しました。

1. **1回目のリマインド**: 稽古日時の何時間前かに送信 (`attendance_reminder_1_hours`)
2. **2回目のリマインド**: 稽古日時の何時間前かに送信 (`attendance_reminder_2_hours`)

## 実装内容と変更点

### 1. データベースの改修とマイグレーション
- `backend/src/db/models.py` において、`TheaterProject` モデルの `attendance_reminder_hours` および `attendance_deadline_reminder_hours` カラムを削除し、新たに `attendance_reminder_1_hours` (デフォルト48時間前) と `attendance_reminder_2_hours` (デフォルト24時間前) を追加。
- `AttendanceEvent` モデルのリマインダー履歴も `reminder_1_sent_at` と `reminder_2_sent_at` に名称変更。
- 上記変更を反映したAlembicマイグレーションスクリプトを生成し、`server_default` と `batch_alter_table` を用いてSQLiteおよびPostgreSQL環境両方で動作するように安全に設計してDBに適用しました。

### 2. バックエンドAPIの更新
- `backend/src/schemas/project.py` および `backend/src/api/projects.py` を更新し、プロジェクトの作成、更新、取得時に新しい「1回目」および「2回目」のリマインダー設定値の入出力を処理するように対応しました。

### 3. 定期実行タスクのリファクタリング
- `backend/src/services/attendance_tasks.py` の `check_deadlines` 関数を以下のロジックにアップデート:
  - 1回目のリマインド: 稽古時間の `{attendance_reminder_1_hours}` 時間前に達している未回答者にDiscord通知。
  - 2回目のリマインド: 稽古時間の `{attendance_reminder_2_hours}` 時間前に達している未回答者にDiscord通知（※すでに「回答済(ok等)」に変わったユーザーには通知されない仕組みが組み込み済です）。

### 4. フロントエンド画面と多言語対応 (i18n)
- `frontend/src/types/index.ts` の型定義に上記2つのカラムを追加。
- `ProjectSettingsPage.tsx` のプロジェクト設定フォーム内に、それぞれの時間数値を個別に入力できるフィールドを追加。
- `ja`, `en`, `ko`, `zhHans`, `zhHant` の全5言語の `translation.json` に「1回目の出欠リマインド」「2回目の出欠リマインド」対応する翻訳キー群を追加し、ユーザー言語設定に応じて自動表記されるように構築しました。

### 5. Discord通知とAPIレスポンスの表示名最適化
- Discord通知メッセージ内で、ユーザーを判別しやすくするため、**「スクリーンネームが登録されている場合は優先的に表示する」**仕組みを全通知機能（脚本、プロジェクト、出欠、調整、予約等）に導入しました。
- `User` モデルに `display_name` プロパティを追加。
- 共通ユーザー情報スキーマ (`UserResponse`) を通じて、フロントエンドの各種UIでもスクリーンネームが反映されるように統一改修を行いました。
- 各種通知（プロジェクト作成・メンバー権限変更・脚本インポートなど）の内容が、閲覧者のタイムゾーンに合わせて自動変換される Discord タイムスタンプ形式であることを確認しました。

## テストと検証結果

- **単体テスト**: `tests/unit/test_attendance_tasks.py` のモックデータを新スキームに適合させ、`check_deadlines` 実行時に予定時刻を過ぎた設定のものだけがDiscord送信APIを呼び出すことを自動テスト (`pytest`) で確認しました。(4/4 Passed)
- **手動・ビジネスロジック検証**:
  - `pending` (未回答) のままであれば2回目の通知処理が適切に動くこと。
  - レスポンスを返した（リアクション等で `pending` から外れた）ユーザーはこのターゲットリストから除外されるため、2回目のリマインドが送信されない要件を自然に満たしていることを確認しました。
