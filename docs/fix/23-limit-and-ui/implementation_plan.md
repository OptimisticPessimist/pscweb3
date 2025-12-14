# 実装計画 - プロジェクト制限修正 & UI改善

## 目的
制限内であるにもかかわらず新規プロジェクトが作成できない問題を修正し、ダッシュボード上で公開プロジェクトを視覚的に区別できるようにする。

## 変更案

### Backend
#### アーキテクチャの変更 (推奨)
長期的な保守性とパフォーマンスを考慮し、**`TheaterProject` テーブルに `is_public` カラムを明示的に追加**することを提案します。
現状の「公開脚本が含まれているか毎回計算する」方式は計算コストが高く、作成時のロジックも複雑になりがちです。

**設計方針:**
1. **DBスキーマ**: `theater_projects` テーブルに `is_public` (Boolean, default=False) を追加。
2. **プロジェクト作成時**:
   - 通常作成: `is_public = False`
   - 公開脚本インポート時: `is_public = True` で作成
3. **状態の同期**:
   - 脚本アップロード/更新時: 脚本が公開設定なら、親プロジェクトの `is_public` を `True` に更新。
   - 脚本削除/非公開化時: プロジェクト内の公開脚本が0になったら、`is_public` を `False` に戻す（オプション、あるいは一度公開したら公開のままとするか要検討）。
1.  **DBスキーマ**: `theater_projects` テーブルに `is_public` (Boolean, default=False) を追加。
2.  **プロジェクト作成時**:
    -   通常作成: `is_public = False`
    -   公開脚本インポート時: `is_public = True` で作成
3.  **状態の同期**:
    -   脚本アップロード/更新時: 脚本が公開設定なら、親プロジェクトの `is_public` を `True` に更新。
    -   脚本削除/非公開化時: プロジェクト内の公開脚本が0になったら、`is_public` を `False` に戻す（オプション、あるいは一度公開したら公開のままとするか要検討）。
    -   **今回はシンプルに**: 「公開脚本が1つでもあればプロジェクトは公開」というルールに基づき、脚本操作時にフラグを更新するロジックを実装します。

#### `src/services/project_limit.py`
- ロジックを大幅に簡素化。
- `SELECT COUNT(*) FROM theater_projects WHERE user_id = ? AND is_public = FALSE` だけで判定可能になります。

#### Public Scripts Enhancement & Layout Fix

## Goal Description
1.  **Layout Consistency**: Display the sidebar and header on `/public-scripts`, `/public-scripts/:id`, and `/manual` pages by wrapping them in the main application layout.
2.  **Project Creation from Public Script**: Add a "Create Project" button to the Public Script Detail page that allows users to create a new project initialized with that script's content.

## User Review Required
> [!IMPORTANT]
> **Authentication for Public Pages**: The sidebar requires user information to display the profile section. If a user is NOT logged in, the sidebar will show only navigation links. This is expected behavior.

## Proposed Changes

### Frontend Routing & Layout
#### [MODIFY] [App.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/App.tsx)
-   Wrap `/public-scripts/*` and `/manual` routes with `AppLayout` (outside of `ProtectedLayout`) so they share the same UI structure.

### Backend: Project Creation with Script Import
#### [MODIFY] [project.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/project.py)
-   Add `source_public_script_id: UUID | None` to `ProjectCreate` schema.

#### [MODIFY] [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
-   Update `create_project` to check for `source_public_script_id`.
-   If provided:
    -   **Restriction**: Force `is_public=False` (ignore user input).
    -   Fetch the source script (verify `is_public=True`).
    -   After project creation, create a new `Script` record in recent project with the source content.

### Frontend: Project Creation UI
#### [MODIFY] [dashboard.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/dashboard/api/dashboard.ts)
-   Update `createProject` to accept `source_public_script_id`.

#### [MODIFY] [DashboardPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/dashboard/DashboardPage.tsx)
-   In `useEffect`, check for `location.state.importScriptId`.
-   If present:
    -   Open the "Create Project" modal.
    -   Pre-fill the project name.
    -   **Disable** the `is_public` checkbox and set it to `false`.
    -   Show a warning: "Imported scripts cannot be republished as public projects."
-   Pass `source_public_script_id` to the mutation.

#### [MODIFY] [PublicScriptDetailPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/public_scripts/pages/PublicScriptDetailPage.tsx)
-   Add "Create Project with this Script" button.
-   On click, navigate to `/dashboard` with `{ state: { importScriptId: script.id, importScriptTitle: script.title } }`.

## Verification Plan
### Manual Verification
1.  **Layout Check**:
    -   Visit `/public-scripts` without login. Verify Sidebar/Header appear (Sidebar should show limited links).
    -   Visit `/manual` without login. Verify Layout.
2.  **Create Project from Script**:
    -   Login.
    -   Go to `/public-scripts`, invalid script.
    -   Click "Create Project".
    -   Verify redirection to Dashboard -> Modal opens -> Name pre-filled.
    -   Submit.
    -   Verify new project is created AND contains the script/scenes.py`
#### `src/api/projects.py` / `src/services/project_service.py`
- プロジェクト作成API (`create_project`) に `is_public` 引数を追加（内部利用のみ、または管理者用）。
- インポート処理ではこのフラグを立ててプロジェクトを作成します。

#### `src/services/script_processor.py`
- 脚本保存時に `project.is_public` を再評価して更新する処理を追加。

### Frontend
#### `src/features/dashboard/pages/DashboardPage.tsx`
- プロジェクトオブジェクトの `is_public` プロパティを直接参照してUIを切り替え可能。シンプルになります。


## 検証計画
- プロジェクト作成制限の手動検証
  - 通常作成時の制限（非公開2つまで）
  - 公開脚本インポート時の制限除外
- ダッシュボードでのUI確認
  - 公開プロジェクトの表示（アイコン/バッジ等）
