# Task: カレンダービューの参加可能メンバーに役職や役名も表示する

## 目標
日程調整のカレンダービューにおいて、参加可能メンバーおよび参加可能かもしれないメンバーのリストに、そのユーザーの役職や役名もあわせて表示する。

## タスクリスト
- [ ] バックエンドの改修
  - [ ] `schemas/schedule_poll.py` の更新: `CalendarMemberInfo` モデルを追加し、`PollCandidateAnalysis` に `available_members` 等のプロパティを追加する。
  - [ ] `schedule_poll_service.py` の更新: カレンダー分析データに役職情報も含めて `CalendarMemberInfo` リストを返すようにする。
- [ ] フロントエンドの改修
  - [ ] `schedulePoll.ts` 内のAPIインターフェース更新: バックエンドスキーマに合わせて `PollCandidateAnalysis` の型を修正。
  - [ ] `SchedulePollCalendar.tsx` の更新: 役職情報をUIに表示するよう改修。
- [ ] ドキュメントの作成とコードレビュー
  - [ ] 実装計画 (`implementation_plan.md`)
  - [ ] コードのセルフレビューと修正
  - [ ] 完了報告 (`walkthrough.md`)
