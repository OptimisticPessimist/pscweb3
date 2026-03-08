# タスクリスト (香盤表のキャラクターソート)

- [x] `backend/src/db/models.py` の `Character` モデルに `order` カラム（Integer）を追加する
- [x] Alembic を使用してマイグレーションスクリプトを自動生成する
- [x] `backend/src/services/fountain_parser.py` を修正し、スクリプトパース時にキャラクターの `order` を決定して DB に保存するロジックを実装する
  - [x] `# 登場人物` セクションの順番を抽出し、最優先の順位とする
  - [x] セリフ発話に基づく初登場順を抽出し、次点の順位とする
  - [x] 最終的に `Character.order` を上記に基づいて安全に割り当てる
- [x] `backend/src/schemas/scene_chart.py` の `CharacterInScene` に `order: int` を追加する
- [x] `backend/src/api/scene_charts.py` のエンドポイントで、`CharacterInScene` を作成する際に `mapping.character.order` を含める
- [x] `frontend/src/features/scene_charts/pages/SceneChartPage.tsx` を修正し、画面上部に描画する全キャラクターリスト (`uniqueChars`) を `order` で昇順にソートする
- [x] 開発サーバーにアクセスして機能をマニュアルテストする
- [x] コードレビューを実行し、結果を `docs/feature/55-sort-characters-in-scene-matrix/code-review.md` に保存する
