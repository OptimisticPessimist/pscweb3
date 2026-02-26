# 日程調整カレンダー シーン絞り込み機能 バグ修正（選択肢が出ない問題の再修正）

- [x] バグの原因特定と修正方針（implementation_plan.md）の作成
- [x] バックエンドの修正
  - [x] `SchedulePollCalendarAnalysis` および `PollSceneInfo` スキーマの追加・変更
  - [x] `schedule_poll_service.py` の `get_calendar_analysis` で全シーン情報を付与して返すように修正
- [x] フロントエンドの修正
  - [x] `schedulePoll.ts` でインターフェースを更新（`all_scenes`の追加）
  - [x] `SchedulePollCalendar.tsx` で `useMemo` による `scenes` の生成ロジックを `all_scenes` 優先に変更
- [ ] 動作確認
  - [ ] 全く「可能」「リーチ」判定のないシーンでもプルダウンに一覧表示されることを検証
- [ ] mainへのマージおよびドキュメント(`walkthrough.md`)更新
