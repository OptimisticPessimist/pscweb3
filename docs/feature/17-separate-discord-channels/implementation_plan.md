# Discord通知チャンネル分離 実装計画

## 目標
脚本のアップロード/更新通知を、他の通知（マイルストーン、メンバー管理など）とは別のチャンネル（Webhook）に送信できるようにする。

## 概要
`TheaterProject` モデルに、脚本通知専用のWebhook URL (`discord_script_webhook_url`) を追加します。
設定画面では、既存の Webhook URL を「一般通知用」、新しい URL を「脚本通知用」として区別します。

## 変更内容

### バックエンド

#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- `TheaterProject` モデルに `discord_script_webhook_url` (String, nullable) を追加。

#### [NEW] [migrations/versions/xxxx_add_script_webhook.py](file:///f:/src/PythonProject/pscweb3-1/backend/migrations/versions/)
- Alembicによるカラム追加マイグレーション。

#### [MODIFY] [project.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/project.py)
- `ProjectUpdate` / `ProjectResponse` に `discord_script_webhook_url` を追加。

#### [MODIFY] [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
- `update_project` で新しいフィールドの更新処理を追加。

#### [MODIFY] [scripts.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/scripts.py)
- `upload_script` 関数内での通知送信先判定ロジックを変更。
  - `project.discord_script_webhook_url` があればそれを使用。
  - なければ `project.discord_webhook_url` を使用（フォールバック）。

### フロントエンド

#### [MODIFY] [index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/types/index.ts)
- `Project` 型に `discord_script_webhook_url` を追加。

#### [MODIFY] [ProjectSettingsPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/pages/ProjectSettingsPage.tsx)
- 入力フィールドを追加し、ラベルを整理。
  - **Script Notification Webhook URL** (New)
  - **General Notification Webhook URL** (Renamed from Webhook URL)
  - **Attendance Notification Channel ID** (Renamed from Channel ID)

## 検証計画
1. マイグレーションを実行。
2. 設定画面で「脚本用Webhook」を設定。
3. 脚本を更新し、指定したWebhookに通知が届くことを確認。
4. マイルストーンを作成し、従来の（一般用）Webhookに通知が届くことを確認。
