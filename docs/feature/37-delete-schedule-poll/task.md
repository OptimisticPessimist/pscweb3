# タスクリスト (機能: 37-delete-schedule-poll)

## 1. 調査・設計
- [x] 現在の実装状況の確認 (DBモデルのカスケード設定チェック)
- [x] 実装計画の作成・ユーザー合意の取得

## 2. API側実装
- [ ] `backend/src/api/schedule_polls.py` に `DELETE /projects/{project_id}/polls/{poll_id}` を実装
  - editor 権限以上のチェック
  - スケジュール調整の削除処理 (`db.delete()`) の追加
  - 返り値として `{ "status": "ok" }` を返す等

## 3. UI/フロントエンド実装
- [ ] `frontend/src/features/schedule_polls/api/schedulePoll.ts` に `deletePoll` 関数を作成
- [ ] `frontend/src/features/schedule_polls/pages/SchedulePollDetailPage.tsx` に削除ボタンを追加
- [ ] 削除ボタンのクリック時に `window.confirm` ダイアログを表示
- [ ] 削除完了後、日程調整一覧ページにリダイレクト (`navigate`) し、React Queryのキャッシュを破棄(`invalidateQueries`)

## 4. テスト・検証
- [ ] ローカル環境でバックエンドAPIが正しく削除（関連レコード含む）を行うかを確認
- [ ] ブラウザ上で詳細ページを開き、削除ボタンを押して一覧に画面が戻り、該当の日程調整が一覧から消えている事を確認

## 5. ドキュメント・仕上げ
- [ ] `walkthrough.md` に結果を記載
- [ ] feature ブランチを push し、マージ
