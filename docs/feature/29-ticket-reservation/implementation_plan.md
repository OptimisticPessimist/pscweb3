# マイルストーンの時間管理と予約情報の強化

## 目標
公演スタッフがマイルストーン（公演）の具体的な開始・終了時間を設定できるようにし、予約完了メールやGoogleカレンダーのイベントにプロジェクト名（公演名）を明確に表示する。

## ユーザー確認事項
なし。

## 変更内容

### Backend
#### [MODIFY] [project.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/project.py)
- `MilestoneCreate` および `MilestoneUpdate` スキーマが `datetime` 入力を正しくサポートしているか確認し、必要に応じて修正する。

#### [MODIFY] [email.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/email.py)
- `send_reservation_confirmation` メソッドを更新し、`project_name` 引数を受け取るようにする。
- メールの件名と本文に `project_name` を含める。

#### [MODIFY] [reservations.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/reservations.py)
- `create_reservation` 内でマイルストーンに関連付けられた `project` を取得する。
- `email_service.send_reservation_confirmation` に `project.name` を渡す。

### Frontend
#### [MODIFY] [MilestoneSettings.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/components/MilestoneSettings.tsx)
- `start_date` と `end_date` の入力タイプを `date` から `datetime-local` に変更する。
- 状態の初期化と変更ハンドラを更新し、日時文字列（YYYY-MM-DDTHH:mm）を適切に処理するようにする。

#### [MODIFY] [ReservationCompletedPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/reservations/pages/ReservationCompletedPage.tsx)
- Googleカレンダーリンク生成時に、イベントタイトルにプロジェクト名を含める（例: `プロジェクト名 - マイルストーン名`）。

## 検証計画
### 手動検証
1.  **マイルストーン作成**: 設定ページから具体的な開始・終了時間を指定して新しいマイルストーンを作成し、正しく保存されることを確認する。
2.  **予約**: そのマイルストーンに対してテスト予約を行う。
3.  **メール**: 受信したメールの件名と本文にプロジェクト名が含まれているか確認する。
4.  **カレンダー**: 完了ページのGoogleカレンダーボタンをクリックし、イベントタイトルにプロジェクト名が含まれ、時間が正しく設定されているか確認する。
