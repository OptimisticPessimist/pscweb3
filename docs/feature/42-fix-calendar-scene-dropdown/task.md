# 日程調整カレンダー シーン絞り込み機能 修正タスク

- [x] バグの原因特定と修正方針（implementation_plan.md）の作成
- [x] `SchedulePollCalendar.tsx` のドロップダウンCSS修正
  - [x] `z-index`の複雑な重なり順の解消
  - [x] formsプラグインのデフォルト背景（矢印）を無効化する `bg-none` クラス等の追加
  - [x] `pointer-events-none` の見直し
- [ ] ブラウザでの動作検証
- [ ] walkthrough.md の作成とmainブランチへのマージ
