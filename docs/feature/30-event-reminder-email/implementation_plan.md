# チケット予約当日通知メール機能 - 実装計画

## 概要
チケット予約完了時に送信される確認メールに加えて、**公演当日の朝（例: 9:00 AM JST）に自動でリマインダーメールを送信**する機能を実装します。

### 目的
- 予約者が公演日を忘れないよう、当日にリマインドする
- 来場率の向上
- ユーザーエクスペリエンスの向上

## 技術的背景

### 使用サービス
- **SendGrid**: 既に予約確認メールで使用中（月25,000通の無料枠）
- **Azure Functions Timer Trigger**: 定期実行タスク（1日1回、朝9時など）
  - Azureの無料枠で利用可能
  - Cronスケジュール設定可能

### 既存の類似実装
- [`attendance_tasks.py`](file:///F:/src/PythonProject/pscweb3-1/backend/src/services/attendance_tasks.py): 出欠確認のリマインダー送信機能
  - 定期的にDBをチェックして条件に合致するイベントに通知を送信
  - 同様のパターンを適用可能

## 提案する変更内容

### 1. Email Service拡張

#### [MODIFY] [`email.py`](file:///F:/src/PythonProject/pscweb3-1/backend/src/services/email.py)

**変更内容:**
- `send_event_reminder`メソッドを追加
- 予約者に対して、当日の公演情報をリマインドするメール本文を作成

**メール内容例:**
```
件名: 【本日開催】{project_name} - {milestone_title} のご案内

{name} 様

本日は{milestone_title}の開催日です。
ご来場をお待ちしております。

━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 公演名: {project_name}
■ マイルストーン: {milestone_title}
■ 日時: {date_str}
■ 会場: {location}
■ 予約枚数: {count} 枚
━━━━━━━━━━━━━━━━━━━━━━━━━━

受付にてお名前をお伝えください。
皆様のご来場を心よりお待ちしております。

※このメールは送信専用アドレスから送信されています。
```

### 2. Reservation Tasks Service作成

#### [NEW] [`reservation_tasks.py`](file:///F:/src/PythonProject/pscweb3-1/backend/src/services/reservation_tasks.py)

**機能:**
- `check_todays_events()`: 当日のMilestoneを取得し、予約者にメールを送信
- ロジック:
  1. 現在時刻（UTC）を取得
  2. 当日（JST基準）のMilestoneを検索
  3. 各Milestoneの予約者リストを取得
  4. 各予約者に対して`send_event_reminder`を呼び出し
  5. 送信済みフラグを管理（重複送信を防ぐ）

**重複送信防止策:**
- `Reservation`テーブルに`reminder_sent`フラグを追加（マイグレーション必要）
- または、送信履歴を別テーブルで管理

### 3. Database Migration

#### [NEW] Alembicマイグレーション

**変更内容:**
- `Reservation`テーブルに`reminder_sent_at: datetime | None`カラムを追加
- 送信済みの場合、送信日時を記録

### 4. 手動実行エンドポイント（オプション）

#### [MODIFY] [`reservations.py`](file:///F:/src/PythonProject/pscweb3-1/backend/src/api/reservations.py)

**変更内容:**
- `POST /api/admin/tasks/send-event-reminders` エンドポイントを追加
- 管理者（owner/editor）のみがアクセス可能
- 手動でリマインダー送信タスクをトリガー

**用途:**
- テスト時の手動実行
- 緊急時の再送信

### 5. Azure Functions Timer Trigger設定

#### [NEW] `function_app.py`の拡張

**Cronスケジュール設定例:**
```python
@app.timer_trigger(schedule="0 0 9 * * *", arg_name="timer", run_on_startup=False)
async def send_event_reminders_timer(timer: func.TimerRequest) -> None:
    """毎日朝9時(UTC)に実行 - イベントリマインダー送信."""
    logging.info("Starting event reminder task...")
    stats = await check_todays_events()
    logging.info(f"Event reminder task completed: {stats}")
```

> **注意:** Cronスケジュールは**UTC時刻**で指定されます。  
> 日本時間（JST）の9:00は、UTCで0:00です。

---

## 検証計画

### 自動テスト

#### ユニットテスト

**[NEW] `tests/unit/test_reservation_tasks.py`**
- `check_todays_events()`のモックテスト
- 当日のReservationが正しく抽出されるか
- メール送信関数が正しく呼ばれるか
- `reminder_sent_at`が正しく更新されるか

**実行方法:**
```powershell
cd backend
pytest tests/unit/test_reservation_tasks.py -v
```

**[MODIFY] `tests/unit/test_email.py`（新規作成）**
- `send_event_reminder()`のモックテスト
- 正しいメール内容が生成されるか

**実行方法:**
```powershell
cd backend
pytest tests/unit/test_email.py::test_send_event_reminder -v
```

#### 統合テスト

**[NEW] `tests/api/test_reservation_reminder.py`**
- 当日のMilestoneと予約を作成
- タスク実行後、`reminder_sent_at`が更新されているか確認
- 既に送信済みの予約に対して重複送信されないか確認

**実行方法:**
```powershell
cd backend
pytest tests/api/test_reservation_reminder.py -v
```

### 手動検証

#### ローカル環境での手動実行

1. `.env`にSendGrid APIキーが設定されていることを確認
2. テスト用のReservationを作成（start_dateを当日に設定）
3. 手動エンドポイントを実行:
   ```powershell
   # FastAPIサーバー起動
   cd backend/src
   uvicorn main:app --reload
   ```
4. 別ターミナルで:
   ```powershell
   # 管理者権限で手動実行エンドポイントを呼び出し
   curl -X POST http://localhost:8000/api/admin/tasks/send-event-reminders `
     -H "Authorization: Bearer {token}"
   ```
5. メールボックスを確認（テスト用メールアドレス）

#### Azure Functions Timer Triggerの検証

1. ローカルでAzure Functions Coreツールを使用:
   ```powershell
   cd backend
   func start
   ```
2. Timer Triggerが正しくスケジュールされているか確認
3. モック時刻を設定して、当日判定ロジックをテスト

---

## ユーザーレビューが必要な項目

> [!IMPORTANT]  
> **重複送信防止の実装方針**  
> `Reservation`テーブルに`reminder_sent_at`カラムを追加することで、送信済みの予約を識別します。これにより、何らかの理由でタスクが複数回実行されても、同じ予約者に重複してメールが送信されることを防ぎます。  
> この変更はデータベーススキーマ変更を伴うため、Alembicマイグレーションが必要です。

> [!IMPORTANT]  
> **Timer Triggerの実行時刻**  
> デフォルトでは**毎日UTC 0:00（JST 9:00）**に実行されるよう設定します。  
> 異なる時刻を希望される場合は、Cronスケジュールを調整してください。

> [!WARNING]  
> **SendGridの無料枠制限**  
> 現在、月25,000通の無料枠を使用しています。予約確認メールに加えて当日通知メールが追加されるため、送信数が増加します。大規模な公演が予定されている場合は、送信数の見積もりを確認してください。

---

## 実装の優先順位

1. **Phase 1（最小実装）:**
   - Email Serviceの拡張
   - Reservation Tasksの作成
   - DBマイグレーション
   - 手動実行エンドポイント
   - ユニットテスト

2. **Phase 2（自動化）:**
   - Azure Functions Timer Triggerの設定
   - 統合テスト
   - 本番環境へのデプロイ

3. **Phase 3（オプション）:**
   - 通知時刻のカスタマイズ機能（プロジェクト設定で調整可能に）
   - 複数言語対応（i18n）
