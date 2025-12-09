# スタッフ管理セクション実装計画

## 目標
サイドバーの「Cast」と「Schedule」の間に「Staff」セクションを追加し、プロジェクトメンバー（スタッフ）の一覧を表示するページを作成する。

## 変更内容

### Frontend

#### [MODIFY] `src/components/layout/Sidebar.tsx`
- メニューに「Staff」を追加（CastとScheduleの間）。
- アイコン案: `Users` (Castで使用中) と区別するため `Wrench` を使用。

#### [NEW] `src/features/staff/pages/StaffPage.tsx`
- 新規ページコンポーネント。
- プロジェクトメンバー一覧を取得 (`GET /projects/{id}/members`)。
- メンバーを表示（ユーザー名、スタッフ役割/Default Staff Role、Discord名）。
- （オプション）役割ごとのグループ化など（今回は単純なリスト表示から開始）。

#### [MODIFY] `src/App.tsx`
- ルート `/projects/:projectId/staff` を追加し、`StaffPage` にマッピング。

#### [NEW] `src/features/staff/index.ts`
- `StaffPage` をエクスポート。

## 検証計画
1.  サイドバーに「Staff」が表示されることを確認。
2.  「Staff」をクリックすると `/projects/{id}/staff` に遷移することを確認。
3.  スタッフページにメンバー一覧と役割が表示されることを確認。
