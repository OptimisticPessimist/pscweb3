# タスクリスト (機能: 36-discord-schedule-notify)

## 1. 調査・設計
- [x] 現在の実装状況の確認 (finalize_poll および update_rehearsal)
- [x] 実装計画の作成・ユーザー合意の取得

## 2. APIの実装
- [ ] `src/api/schedule_polls.py` の `finalize_poll` に Discord 通知処理を追加
  - 引数に `discord_service`, `background_tasks` を追加
  - 稽古スケジュールの自動作成後、プロジェクトのWebHook URL宛に作成通知を非同期送信
- [ ] `src/api/rehearsals.py` の `update_rehearsal` に Discord 通知処理を追加
  - 引数に `discord_service`, `background_tasks` を追加
  - 更新された内容を元に、関係者（メンション付き）へ更新通知を作成・送信

## 3. テスト・検証
- [ ] ローカル環境で `finalize_poll` (日程調整確定) が正常に動作し、Discordへ通知が送られるか確認 (手動またはモックテスト)
- [ ] ローカル環境で `update_rehearsal` (稽古更新) が正常に動作し、Discordへ通知が送られるか確認 (手動またはモックテスト)
- [ ] エラーが出ないかCI/CDを通す

## 4. ドキュメント作成
- [ ] `walkthrough.md` に実装・検証・レビュー結果を記述
- [ ] ブランチをpushし、PR作成の準備 (あるいは通知して作業完了)
