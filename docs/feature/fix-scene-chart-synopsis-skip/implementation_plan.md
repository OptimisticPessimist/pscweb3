# 実装計画：シーンチャートのシノプシス除外の確認とクリーンアップ

ユーザーから報告されたテスト失敗 `test_generate_scene_chart_skips_synopsis` について調査した結果、直近のコミットで `scene_number <= 0` のチェックが追加されており、現在の `main` ブランチベースでは解決済みであることを確認しました。
本タスクでは、その修正が正しく機能していることを再確認し、デバッグ用のプリントの削除などのクリーンアップを行います。

## 変更内容

### 香盤表生成サービス

#### [MODIFY] [scene_chart_generator.py](backend/src/services/scene_chart_generator.py)
- デバッグ用の `print` 文を削除します。
- ロジック（`scene.scene_number <= 0` のスキップ）は維持します。

## 検証計画

### 自動テスト
- `pytest tests/unit/test_synopsis_logic.py` を実行し、当該テストがパスすることを確認します。
- `pytest tests/unit/test_scene_chart_generator.py` を実行し、既存の香盤表生成テストに影響がないことを確認します。

### 手動確認
- 特になし（単体テストで十分検証可能）。
