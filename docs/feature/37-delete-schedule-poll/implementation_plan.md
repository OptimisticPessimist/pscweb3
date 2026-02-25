# 実装計画: 日程調整の削除機能追加 (機能: 37-delete-schedule-poll)

## 目的
作成した日程調整（Schedule Poll）を後から削除できるようにする。現在、誤って作成した調整や不要になった調整をユーザーが消すためのUIおよびAPIエンドポイントが存在しないため、これを追加する。

## 確認事項
- **削除処理の権限について**:
  - `ProjectMember` の役割が `editor` 以上のメンバーにのみ削除を許可する仕様とします。
- **削除の仕様**:
  - バックエンドでは、削除した際に関連する候補日(`SchedulePollCandidate`)と回答(`SchedulePollAnswer`)がDBのカスケード削除により自動的に削除されるように実装します。
  - フロントエンドでは、削除時に確認ダイアログ（`window.confirm`などで「本当に削除しますか？」）を表示します。

## 変更内容提案 (Proposed Changes)

### バックエンド側
#### `backend/src/api/schedule_polls.py`
- `@router.delete("/projects/{project_id}/polls/{poll_id}")` のエンドポイントを追加。
- 認証と権限チェック（`editor` 以上）を実施。
- `SchedulePoll` モデルから `poll_id` のレコードを取得し、存在チェック。
- `await db.delete(poll)` を実行し、`await db.commit()`。

### フロントエンド側
#### `frontend/src/features/schedule_polls/api/schedulePoll.ts`
- `deletePoll` 関数（DELETE `/api/projects/{projectId}/polls/{pollId}`）を追加。

#### `frontend/src/features/schedule_polls/pages/SchedulePollDetailPage.tsx`
- ヘッダーまたはアクションエリア周辺に「削除 (Delete)」ボタンを追加。
- 削除ボタンが押下された際に確認ダイアログを表示。
- OKが押されれば `deletePoll` を実行し、成功時に `SchedulePollListPage` へ遷移（`navigate("/projects/${projectId}/polls")`）。
- 一覧へ戻る前に `queryClient.invalidateQueries` を行い、一覧のキャッシュを更新して削除を反映させる。

## 検証計画
- FastAPI上で削除APIを呼び出し、削除が正しくDBに反映され、連携する回答データなどが破棄されることを確認する。
- フロントエンドにて、削除ボタンのUIが表示され、ダイアログによる確認と遷移が正しく行われることを確認する。
