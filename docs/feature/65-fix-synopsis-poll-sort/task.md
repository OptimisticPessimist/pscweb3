# タスク: あらすじ表示修正および香盤表ソート順変更

## 概要
- あらすじ部分に登場人物が入り込んでしまう問題を修正
- 香盤表（Scene Chart）を Act 順、次に Scene 順でソートするように変更

## タスクリスト
- [x] `backend/src/services/fountain_parser.py` の修正
  - [x] セクション見出し（登場人物セクション含む）で説明収集を停止するガードを追加
- [x] `backend/src/api/scene_charts.py` の修正
  - [x] レスポンスのソート順を `(act_number, scene_number)` に変更
  - [x] レスポンスに `scene_id` を追加
- [x] `backend/src/db/models.py` の修正
  - [x] `Script.scenes` および `Scene.lines` のリレーションに `order_by` を追加
- [x] `backend/src/schemas/scene_chart.py` の修正
  - [x] `SceneInChart` スキーマに `scene_id` を追加
- [x] `frontend/src/types/index.ts` の修正
  - [x] `SceneInChart` 型に `scene_id` を追加
- [x] `frontend/src/features/scene_charts/pages/SceneChartPage.tsx` の修正
  - [x] ループの `key` を `scene_id` に変更
- [x] バックエンドテストの実行
  - [x] `test_fountain_parser.py` にあらすじ収集の境界テストを追加し、パスすることを確認
