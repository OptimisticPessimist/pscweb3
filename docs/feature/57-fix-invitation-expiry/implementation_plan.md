# 招待URLが期限前に消える問題の修正と一覧表示機能の追加

## 概要
招待URLが期限内であるにもかかわらず、設定画面から消えてしまう問題を修正します。
現状、招待URLの一覧を取得するAPIが存在せず、フロントエンドでも最後に生成したURLのみをメモリ上で保持しているため、画面の刷新や遷移でURLが表示されなくなっていました。

本修正では、プロジェクトごとの有効な勧誘URL一覧を取得するAPIを追加し、フロントエンドでこれらを一覧表示するように変更します。

## ユーザーレビューが必要な事項
- 特になし

## 提案される変更

### 招待URL一覧取得APIの追加

#### [MODIFY] [invitations.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/invitations.py)
- `GET /projects/{project_id}/invitations` エンドポイントを追加します。
- 以下の条件に合致する招待URLのみを返すようにフィルタリングします：
    - 有効期限内 (`expires_at > now`)
    - 使用回数が上限に達していない (`max_uses is None` or `used_count < max_uses`)

### フロントエンドの修正

#### [MODIFY] [invitations.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/api/invitations.ts)
- `apiClient.get` を使用して `/projects/${projectId}/invitations` から一覧を取得する `getProjectInvitations` メソッドを追加します。

#### [MODIFY] [InvitationPanel.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/components/InvitationPanel.tsx)
- `@tanstack/react-query` の `useQuery` を使用して、コンポーネントマウント時に有効な招待URL一覧を取得します。
- 取得した一覧をテーブル形式で表示します。
- 新規リンク生成成功時に、クエリを無効化（invalidateQueries）して一覧を最新化します。

## 検証プラン

### 自動テスト
- `backend/tests/integration/test_api_invitations.py` に以下のテストを追加します：
    - `test_list_project_invitations`: 期待通りにアクティブな招待URLのみがリストされるか。
    - 実行コマンド: `pytest backend/tests/integration/test_api_invitations.py`

### 手動確認
1. プロジェクト設定画面の「招待」セクションを表示。
2. 招待リンクを生成し、リストに即座に反映されることを確認。
3. ページをリロードし、生成したリンクが消えずに表示されていることを確認。
4. 複数のリンクを生成し、すべてがリストに表示されることを確認。
5. （可能であれば）DB上で期限切れにしたURLがリストから消えることを確認。
