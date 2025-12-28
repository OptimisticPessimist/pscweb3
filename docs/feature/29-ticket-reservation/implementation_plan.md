# 実装計画: チケット予約システム

## 概要
公演（マイルストーン）に対して、メールアドレスのみで簡易的にチケット予約ができるシステムを構築します。
予約時には「誰の紹介か（キャスト・スタッフ）」を選択可能とし、管理画面では予約者一覧の確認と出欠管理、および一斉メール送信（アンケート送付等）を可能にします。

## ユーザー確認事項 (解決済み)
以下の点について方針を決定しました。

> [!NOTE]
> **1. 定員（在庫）管理について**
> - **方針**: `milestones` テーブルに `reservation_capacity` カラムを追加し、定員管理を行う。
> - 後から変更可能にする。

> [!NOTE]
> **2. メール送信機能について**
> - **方針**: **SendGridによる自動返信メール**を実装する。
> - 予約完了時に、入力されたメールアドレスへ確認メールを自動送信する。
> - 一斉送信（アンケート等）については、引き続きCSVダウンロード運用とする（SengGridの無料枠温存とリスク回避のため）。

> [!NOTE]
> **3. 紹介者リストについて**
> - **方針**: デフォルトはプロジェクト参加者全員。
> - オプションで「役者(Cast)のみ」に絞り込む機能を実装する（`CharacterCasting` テーブルに紐づくユーザーを抽出）。

> [!NOTE]
> **4. 出欠管理の権限**
> - **方針**: 管理者だけでなく、プロジェクトメンバー（`viewer`以上）であれば誰でも閲覧・更新可能にする。

> [!NOTE]
> **5. カレンダー連携について**
> - **既存ユーザー（ログイン中）**: 予約データにユーザーIDを紐付け、アプリ内のスケジュールに自動表示する。
> - **一般ユーザー**: 予約完了画面に「Googleカレンダーに追加」ボタンを表示する。

## 提案する変更内容

### 1. データベース (PostgreSQL)
**新規テーブル**: `reservations`
| カラム名 | 型 | 説明 |
| :--- | :--- | :--- |
| `id` | `UUID` | PK |
| `milestone_id` | `UUID` | 対象の公演 (FK -> `milestones.id`) |
| `referral_user_id` | `UUID` | 紹介者 (FK -> `users.id`, Nullable) |
| `name` | `String` | 予約者名 (ハンドルネーム可) |
| `email` | `String` | 連絡先メールアドレス |
| `count` | `Integer` | 予約人数 (1-4名) |
| `attended` | `Boolean` | 出席済みフラグ (Default: False) |
| `user_id` | `UUID` | アプリ内ユーザーID (Nullable, ログイン時のみ) |
| `created_at` | `DateTime` | 予約日時 |

**既存テーブル変更**: `milestones`
- `reservation_capacity`: `Integer` (Nullable) - 予約定員数。Nullの場合は無制限。

### 2. バックエンド (FastAPI)
- **Email Service** (SendGrid)
    - `src/services/email.py`: SendGrid APIを使用したメール送信ロジック
    - 環境変数: `SENDGRID_API_KEY`, `FROM_EMAIL`
- **Public API** (認証不要)
    - `POST /api/public/milestones/{id}/reservations`: 予約作成
        - 定員チェック
        - 予約データ保存
        - **確認メール送信 (BackgroundTasks)**
    - `GET /api/public/projects/{id}/members`: 紹介者リスト取得
- **Internal API** (認証必須)
    - `GET /api/projects/{id}/reservations`: 予約一覧取得
    - `PATCH /api/reservations/{id}/attendance`: 出欠フラグ更新
    - `POST /api/projects/{id}/reservations/export`: CSV一斉ダウンロード

### 3. フロントエンド (React)
- **Public Page**: `src/pages/public/TicketReservationPage.tsx`
    - マイルストーン選択、定員チェック
    - 紹介者フィルタリング
    - **完了画面 (`ReservationCompletedPage`)**
        - 「Googleカレンダーに追加」ボタン設置
- **Reservation Management Page**: `src/features/reservations/pages/ReservationListPage.tsx`
    - 予約リスト、出欠管理、CSVダウンロード、定員設定

## 検証計画
### 自動テスト
- APIのユニットテスト（定員オーバー時のエラー挙動含む）
- キャストフィルタリングのロジックテスト

### 手動検証
1. 定員1名のマイルストーンを作成し、2人目が予約しようとした時にエラーになるか。
2. キャストとして配役されたユーザーのみがフィルタリングされるか。
3. CSVダウンロードしたファイルが文字化けせず開けるか。
4. `viewer` 権限のユーザーでログインし、出欠変更ができるか。
