# Azure Functions Timer通知機能 実装ウォークスルー

## 概要
出欠確認の回答期限が過ぎた場合に、未回答のメンバーに対してDiscord通知を自動送信するTimer Functionを実装しました。

## 実装内容

### 1. Azure Functions 設定ファイル
| ファイル | 説明 |
|---------|------|
| [host.json](file:///f:/src/PythonProject/pscweb3-1/backend/host.json) | Azure Functionsホスト設定 |
| [function_app.py](file:///f:/src/PythonProject/pscweb3-1/backend/function_app.py) | FastAPIラッパー & Timer Trigger定義 |

### 2. データベーススキーマ変更
- **変更ファイル**: [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- **追加カラム**: `reminder_sent_at` (リマインダー送信日時)

### 3. Timer Functionロジック
- **新規ファイル**: [attendance_tasks.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/attendance_tasks.py)
- **機能**:
  - 30分ごとに実行
  - 期限切れ かつ 未完了 かつ 未通知のイベントを検索
  - PendingユーザーにメンションしたリマインダーをDiscord送信
  - 送信後 `reminder_sent_at` を更新して重複通知を防止

### 4. テスト
- **テストファイル**: [test_attendance_tasks.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/test_attendance_tasks.py)
- **テストケース**:
  - 期限切れイベントがない場合
  - リマインダー送信成功
  - 未回答ユーザーがいない場合
  - DiscordチャンネルID未設定の場合

## 検証結果
```
tests/test_attendance_tasks.py::test_check_deadlines_no_events PASSED
tests/test_attendance_tasks.py::test_check_deadlines_send_reminder PASSED
tests/test_attendance_tasks.py::test_check_deadlines_no_pending_users PASSED
tests/test_attendance_tasks.py::test_check_deadlines_no_discord_channel PASSED
```

## 次のステップ
1. Azure Function Appリソースの作成
2. GitHub Actionsまたは手動でAzureへデプロイ
3. Azure Portalの Log Stream でTimer実行を確認
