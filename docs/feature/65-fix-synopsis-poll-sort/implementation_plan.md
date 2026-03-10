# 実装計画: あらすじ表示修正および香盤表ソート順変更

## 1. 現状の課題
- **あらすじの重複**: Fountain パーサーがシーン冒頭の説明（Synopsis/Action）を収集する際、後続の「登場人物」セクションの見出しや内容まで収集してしまい、UI上でキャラクター名が2回表示される。
- **ソート順**: 香盤表が `scene_number` のみでソートされており、Act（幕）を跨ぐ場合に表示順が正しくない。

## 2. 修正方針
### バックエンド
- `fountain_parser.py`:
  - `element_type == "Section Heading"` を検出し、それがシーンとして扱われない場合は `collecting_description` を `False` にセットして収集を停止する。
- `scene_charts.py`:
  - シーンのリストをソートする際、キーを `(act_number or 0, scene_number)` とし、幕の概念に対応させる。
  - レスポンスの各シーン要素に `scene_id` を含める。
- `models.py`:
  - SQLAlchemy のリレーションに `order_by` を定数として定義し、常に期待される順序でロードされるようにする。

### フロントエンド
- `types/index.ts`:
  - `SceneInChart` インターフェースをバックエンドの変更に合わせて更新。
- `SceneChartPage.tsx`:
  - レンダリング時の `key` を `scene_id` に変更し、リストの安定性を確保。

## 3. テスト計画
- 既存の `backend/tests/unit/test_fountain_parser.py` を実行。
- 新たに `test_parse_fountain_synopsis_does_not_collect_characters` テストケースを追加し、あらすじ収集がセクション見出しで止まることを検証。
