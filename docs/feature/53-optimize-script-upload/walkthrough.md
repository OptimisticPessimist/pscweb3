# 修正内容の確認 (Walkthrough) - 脚本アップロードの最適化

## 修正の概要
脚本アップロード時の 500 Internal Server Error（タイムアウト等）を解消するため、データベース操作のボトルネックを排除しました。

## 修正内容
1.  **データベース通信の削減**:
    *   `fountain_parser.py`: ループ内での `db.flush()` を削除。代わりに UUID を Python 側で事前生成するように変更。
    *   `scene_chart_generator.py`: 冗長な `db.flush()` を削除。
2.  **トランザクション管理の改善**:
    *   `script_processor.py`: 解析中の個別コミットを廃止し、全ての処理が完了した後に一括してコミットを行うように変更。これにより、不完全なデータが残るのを防ぎつつパフォーマンスを向上。

## 修正後の動作確認 (Proof of Work)

### 1. ユニットテスト
以下のテストを実行し、全てパスすることを確認しました。
- `backend/tests/unit/test_fountain_parser.py`
- `backend/tests/unit/test_scene_chart_generator.py`

#### テスト結果
```text
======================= 15 passed in 0.69s =======================
```

### 2. 修正されたロジックのポイント
- `Character`, `Scene`, `Line` などの大量のデータが生成される際、DBへの往復（RTT）を最小限に抑えています。
- UUID の事前生成により、DBからのID取得を待たずに親子の紐付けを行えるように改善しました。
