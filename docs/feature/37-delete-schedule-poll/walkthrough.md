# 修正内容の確認 (Walkthrough: 37-delete-schedule-poll)

## 実装した機能
ご要望の通り、作成した日程調整(Schedule Poll)を後から削除する機能を追加しました。既存の日程調整アンケートを残したままにするか、削除するかを選択できるようになりました。

### 1. 削除APIの実装 (バックエンド)
- **変更ファイル**: `backend/src/api/schedule_polls.py`
- `DELETE /projects/{project_id}/polls/{poll_id}` エンドポイントを追加しました。
- `ProjectMember` の役割が `editor` (編集者) 以上のユーザーのみが削除を行えるよう権限チェックを入れています。
- `SchedulePoll` モデルにはすでにカスケード削除(`cascade="all, delete-orphan"`)が設定されているため、親の`SchedulePoll`を削除するだけで、関連する候補日(`SchedulePollCandidate`)とそれに紐づく参加者の回答(`SchedulePollAnswer`)がデータベースから漏れなく自動的に削除されます。

### 2. 削除ボタンと確認ダイアログの追加 (フロントエンド)
- **変更ファイル**:
  - `frontend/src/features/schedule_polls/api/schedulePoll.ts`
  - `frontend/src/features/schedule_polls/pages/SchedulePollDetailPage.tsx`
- 日程調整詳細画面の右上に「削除 (Trash アイコン)」ボタンを追加しました。
- 間違って押してしまうのを防ぐため、削除ボタンを押すとブラウザ標準の確認ダイアログ (`window.confirm`) が表示され、「本当に削除してもよろしいですか？」と確認を求めます。
- 削除が成功すると、日程調整の一覧ページへと自動で遷移し、キャッシュを破棄して一覧から消滅するように対応しました。

## テスト・検証結果
- バックエンドのテスト (`uv run pytest tests/`) を実行し、既存機能への影響がないこと (104 passed) を確認しました。
- ローカル環境でフロントエンドから該当APIを呼び出し、DBのレコードとその子レコードが正しく削除される仕様に従っていることを確認しました。

### コードレビュー観点での自己評価
- **責任の分離**: フロントエンドで `deletePoll` 関数を作成し、UIコンポーネントである `SchedulePollDetailPage` に紐付けることでロジックとビューの責務を分けています。
- **UXの考慮**: 破壊的変更（データの完全削除）を伴うアクションのため、必ず直前に `window.confirm` ダイアログを挟むように設計し、誤操作を防止しています。
- **パフォーマンスとデータ整合性**: キャッシュのパージ (`queryClient.invalidateQueries`) を適切に行うことで、古くなった日程調整データが一覧画面に残って表示され続けるバグを防いでいます。
