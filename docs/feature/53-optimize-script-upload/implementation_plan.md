# 脚本アップロードの最適化（500エラー対策）

脚本アップロード時に発生している 500 Internal Server Error（特にタイムアウトが懸念されるケース）を解消するため、データベース操作の最適化を行います。

## 現状の課題
- `fountain_parser.py` において、各行や各シーンの処理ごとに `db.flush()` が呼び出されており、リモートDB（Azure/Neon）との通信遅延（RTT）が累積してタイムアウトを引き起こしている。
- `parse_and_save_fountain` 内で個別に行われている `db.commit()` により、処理が中断された際に中途半端なデータが残るリスクがある。

## 提案される変更点

### [Component] Backend / API & Services

### [Component] Backend / Services

#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- `Scene`, `Character`, `Line` の ID を Python の `uuid.uuid4()` で事前に生成するように変更。
- ループ内および各要素生成直後の `await db.flush()` をすべて削除。
- 最終的な `db.flush()` のみを残し、一括でDBに送るように改善。

#### [MODIFY] [script_processor.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/script_processor.py)
- `parse_and_save_fountain` 内の `db.commit()` を削除し、解析後の `process_script_upload` の最後で一括コミットするように変更。
- 解析およびデータ紐付け完了までを一つのトランザクションにまとめる。

#### [MODIFY] [scene_chart_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/scene_chart_generator.py)
- 冗長な `db.flush()` を整理（削除後のフラッシュはユニーク制約回避のため維持）。

## 検証計画
- 最適化によりアップロードが正常完了し、既存の成功時 Discord 通知が正しく送信されることを確認。

## 検証計画

### 自動テスト
- `pytest tests/unit/services/test_script_processor.py` を実行し、既存の解析ロジックが壊れていないことを確認。
- 香盤表生成テスト `pytest tests/unit/services/test_scene_chart_generator.py` を実行。

### 手動検証
- 実際に脚本（Fountainファイル）をアップロードし、500エラーが発生せずに完了することを確認。
- ログを確認し、DB操作が効率化されていることを確認。
