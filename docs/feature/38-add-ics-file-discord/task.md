# タスクリスト (機能: 38-add-ics-file-discord)

## 1. 調査・設計
- [x] 既存の `add_rehearsal` における ICS ファイル生成ロジックの確認
- [x] 更新 (`update_rehearsal`) および 日程調整確定 (`finalize_poll`) での適用箇所の特定

## 2. 実装: `rehearsals.py` (スケジュール更新時)
- [ ] `update_rehearsal` メソッド内の Discord 通知送信処理前に、ICSファイル構造（`BEGIN:VCALENDAR`...）の生成ロジックを追加
- [ ] イベント内容を「稽古の更新」など適切に表現
- [ ] `discord_service.send_notification` へ `file=ics_file` を渡す

## 3. 実装: `schedule_polls.py` (日程調整からの確定時)
- [ ] `finalize_poll` メソッド内の Discord 通知送信処理前に、ICSファイル構造の生成ロジックを追加
- [ ] イベント内容を「稽古が確定」など適切に表現
- [ ] `discord_service.send_notification` へ `file=ics_file` を渡す
- [ ] `datetime` 等必要なモジュール（`datetime`, `timedelta`等）がインポートされていなければ追加

## 4. テスト・検証
- [ ] 単体テスト・結合テスト (`pytest`) を実行し、既存コードに悪影響がないか確認

## 5. ドキュメント作成とPush
- [ ] `walkthrough.md` 等に変更内容を記録
- [ ] git commit, merge main, push
