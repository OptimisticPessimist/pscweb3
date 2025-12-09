# Staff Management Section Implementation

## 概要
サイドバーに新しく「Staff」セクションを追加し、プロジェクトメンバー（スタッフ）の一覧を表示する機能を実装しました。

## 実装内容
### 1. Sidebar Changes
- **MenuItemの追加**: 「Cast」と「Schedule」の間に「Staff」を追加しました。
- **Icon**: `lucide-react` の `Wrench` アイコンを使用しました。

### 2. Staff Page (`/projects/:projectId/staff`)
- **コンポーネント**: `StaffPage.tsx` を新規作成しました。
- **機能**:
  - `GET /projects/:id/members` からメンバー情報を取得。
  - メンバーの Discordアイコン、ユーザー名、プロジェクト権限 (Owner/Editor/Viewer) を表示。
  - **Default Staff Role** (例: Director, Lighting) をバッジ形式で強調表示。
  - **表示名 (Display Name)**: Discordのユーザー名とは別に、プロジェクト内での表示名を設定可能。
  - **編集機能 (オーナーのみ)**: 一覧上で「Default Staff Role」および「Display Name」を編集・保存可能。
  - 連絡先として Discord username を表示。

## Verification
- **確認手順**:
  1. プロジェクトを選択し、サイドバーの「Staff」をクリック。
  2. メンバー一覧が表示されることを確認。
  3. 各メンバーの役割 (Role) やスタッフ役職 (Staff Role) が正しく表示されていることを確認。
