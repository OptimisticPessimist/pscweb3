# 招待リンク削除機能の追加

## 概要
作成済みの招待リンクを管理者が手動で削除（無効化）できる機能を追加します。
誤って作成した場合や、特定のリンクを即座に無効にしたい場合に対応します。

## Proposed Changes

### バックエンド
- **[MODIFY] [invitations.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/invitations.py)**
    - `DELETE /invitations/{token}` エンドポイントの追加。
    - 権限チェック：
        - 招待リンクの作成者本人
        - または、そのプロジェクトの `owner` または `admin` 権限を持つユーザー
    - 物理削除（レコードの削除）を行います。

### フロントエンド
- **[MODIFY] [invitations.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/api/invitations.ts)**
    - `deleteInvitation(token: string)` メソッドの追加。
- **[MODIFY] [InvitationPanel.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/components/InvitationPanel.tsx)**
    - 招待リンク一覧のテーブルに「削除」アクションを追加。
    - 削除実行前に確認ダイアログを表示。
    - 削除成功時にクエリを無効化して一覧を再取得。

## Verification Plan

### Automated Tests
- `uv run pytest backend/tests/integration/test_api_invitations.py` に削除機能のテストケースを追加。
    - 権限があるユーザーによる削除。
    - 権限がないユーザーによる削除の拒否。

### Manual Verification
- 招待リンクを生成し、一覧に表示されることを確認。
- 削除ボタンをクリックし、確認後に一覧から消えることを確認。
- 削除したトークンで参加を試み、404エラー（または無効エラー）になることを確認。
