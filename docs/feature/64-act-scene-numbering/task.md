# 64-act-scene-numbering

## 概要
台本の採番をActごとにSceneを1から振り直すように修正し、日程調整などのシーン選択画面で `{Act}-{Scene}` という形式で表示する。

## タスクリスト

- [x] `backend/src/services/fountain_parser.py` の修正
  - [x] 新しいAct（幕）が検出された際に `scene_number` を0にリセットする処理を追加する
- [x] `backend/tests/unit/test_fountain_parser.py` の修正
  - [x] 複数のActをまたぐテストデータを追加し、シーン番号がリセットされることを検証するテストケースを追加する
- [x] バックエンドのDiscord通知の修正
  - [x] `backend/src/api/rehearsals.py` (稽古追加・更新時のシーン表記を `{Act}-{Scene}` にする)
  - [x] `backend/src/api/schedule_polls.py` (日程調整確定や出欠確認の通知にシーン情報を含め、`{Act}-{Scene}` 形式にする)
- [x] `frontend/src/utils/sceneFormatter.ts` の作成
  - [x] `actNumber` と `sceneNumber` を受け取り、`{Act}-{Scene}` または `{Scene}` の形式の文字列を返すユーティリティ関数 `formatSceneNumber` を作成する
- [x] 画面表示の修正 (frontend)
  - [x] `frontend/src/features/scripts/pages/ScriptDetailPage.tsx`
  - [x] `frontend/src/features/scripts/pages/PublicScriptPage.tsx`
  - [x] `frontend/src/features/public_scripts/pages/PublicScriptDetailPage.tsx`
  - [x] `frontend/src/features/schedule/components/RehearsalModal.tsx`
  - [x] `frontend/src/features/scene_charts/pages/SceneChartPage.tsx`
  - [x] `frontend/src/features/schedule_polls/pages/SchedulePollDetailPage.tsx`
  - [x] `frontend/src/features/schedule_polls/components/SchedulePollCalendar.tsx`
- [x] バックエンドのテスト実行 (`pytest backend/tests/unit/test_fountain_parser.py -v`)
- [x] フロントエンドのビルドテスト (`npm run build`)
- [x] コードレビューの実施と `walkthrough.md` の作成
