# タスクリスト: 脚本アップロードの最適化

- [x] 最適化方針の検討
- [x] 実装
    - [x] `fountain_parser.py`: `db.flush()` の削除とUUID事前生成の導入
    - [x] `script_processor.py`: トランザクション管理の改善（一括コミット）
    - [x] `scene_chart_generator.py`: `db.flush()` の整理
- [x] 検証
    - [x] ユニットテスト実行
    - [x] 手動アップロードテスト（ログレベルでの確認）
- [x] 完了報告
