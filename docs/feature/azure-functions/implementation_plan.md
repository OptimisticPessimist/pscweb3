# Azure Functions デプロイ & タイマー通知機能 実装計画

## 目的
既存のFastAPIバックエンドを **Azure Functions** にデプロイし、出欠確認の回答期限が過ぎたにもかかわらず未回答のメンバーに対して自動的にDiscord通知を送る **Timer Function** を実装します。

## ユーザー確認事項
> [!IMPORTANT]
> **データベーススキーマ変更**: 重複通知を防ぐため、`attendance_events` テーブルに `reminder_sent_at` カラムを追加します。
> **Azureリソース**: Azure Function App（無料枠には従量課金プランが推奨）と、適切に設定された `AzureWebJobsStorage` 接続文字列が必要です。

## 変更内容

### バックエンド インフラ (`backend/`)
#### [NEW] [function_app.py](file:///f:/src/PythonProject/pscweb3-1/backend/function_app.py)
 - Azure Functions v2 プログラミングモデルのエントリーポイント。
 - `AsgiFunctionApp` を使用してFastAPIアプリをラップし、HTTPリクエストを処理します。
 - `schedule_attendance_reminder` タイマートリガーを定義します（30分ごとに実行）。

#### [NEW] [host.json](file:///f:/src/PythonProject/pscweb3-1/backend/host.json)
 - Azure Functions ホストの設定ファイル（ログ設定、拡張機能バンドルなど）。

### データベーススキーマ (`backend/src/db/models.py`)
#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
 - `AttendanceEvent` モデルに `reminder_sent_at: Mapped[datetime | None]` を追加します。

#### [NEW] Migration Script
 - スキーマ変更を適用するためのAlembicマイグレーションスクリプトを作成します。

### サービスロジック (`backend/src/services/scripts/`)
#### [NEW] [attendance_tasks.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/attendance_tasks.py)
 - 期限切れかつ未通知のイベントを検索し、Discord通知を送信するロジック。
 - 既存の `DiscordService` とデータベース依存関係を再利用します。
 - **ロジック詳細**:
   1. `deadline <= 現在時刻` かつ `reminder_sent_at IS NULL` である `AttendanceEvent` をクエリします。
   2. 各イベントについて:
      a. `status == 'pending'` のターゲットユーザーを取得します。
      b. Discordメッセージを送信します（既存の `remind_pending_users` ロジックを再利用）。
      c. `reminder_sent_at` を現在時刻で更新します。

## 検証計画

### 自動テスト
- `attendance_tasks.py` のユニットテストを作成し、DBとDiscordサービスをモック化してテストします。
- `check_deadlines` ロジックが正しく期限切れイベントを特定できることを検証します。

### 手動検証
1. **ローカルでのFunction実行**:
   - `func start` コマンドを使用してロジックをローカルで実行します。
   - 手動で「期限が1分後」のイベントを作成します。
   - タイマーが発火するのを待つ（またはHTTP管理者エンドポイント経由で手動トリガーする）し、Discordメッセージが送信されることを確認します。
2. **Azureへのデプロイ**:
   - Azure Functionsへデプロイします。
   - Azure Portalの `Log Stream` を確認し、タイマーが定期実行されていることを確認します。
