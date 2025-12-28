# Milestone Capacity Management Description

## 目標
1.  **予約状況の表示**: マイルストーン設定画面で「現在の予約数 / 予約定員」を表示する。
2.  **定員の変更**: マイルストーン設定画面から予約定員（最大数）を変更可能にする。
3.  **予約一覧への導線**: マイルストーンごとに「予約一覧」ページへのリンクを設置する。

## 変更内容

### Backend
#### [MODIFY] [project.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/project.py)
- `MilestoneUpdate` スキーマを作成（`reservation_capacity` 等を更新可能に）。
- `MilestoneResponse` に `current_reservation_count: int` を追加。

#### [MODIFY] [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
- `list_milestones`: `Reservation` を外部結合し、`sum(Reservation.count)` で現在の予約総数を計算して返却するように変更（`group_by` Milestone.id）。
- `update_milestone`: `PATCH /projects/{project_id}/milestones/{milestone_id}` エンドポイントを追加。
    - `MilestoneUpdate` スキーマを受け取り、該当マイルストーンを更新する。

### Frontend
#### [MODIFY] [types/index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/types/index.ts)
- `Milestone` 型に `current_reservation_count` を追加。

#### [MODIFY] [projects.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/api/projects.ts)
- `updateMilestone` メソッドを追加 (`PATCH`).

#### [MODIFY] [MilestoneSettings.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/components/MilestoneSettings.tsx)
- マイルストーン一覧項目の表示を更新。
- **予約数表示**: `current_reservation_count` / `reservation_capacity` (または "無制限") を表示。
- **定員編集**:
    - `reservation_capacity` 部分をクリックまたは編集アイコンで、インライン編集モードにする（または常時Input）。
    - 変更を保存 (`onBlur` または保存ボタン)。
- **予約一覧リンク**:
    - 各項目の適当な場所（アクションボタン列など）に「予約者一覧」ボタンを追加。
    - リンク先: `/projects/{projectId}/reservations?milestoneId={milestone.id}` (もしフィルタパラメータがあれば。なければ `/projects/{projectId}/reservations`)

## 検証計画
1.  **表示確認**: 予約済みマイルストーンで「予約数 / 定員」が正しく表示されるか。
2.  **定員変更**: UIから定員を変更し、リロード後も反映されているか。
3.  **リンク遷移**: 「予約者一覧」をクリックして、正しい一覧ページ（できればフィルタ済み）に遷移するか。
