# Fountain脚本メタデータのサポート

目的: Fountain形式の脚本からメタデータ（日付、リビジョン、メモなど）をパースし、データベースに保存する。

## 変更内容

### データベーススキーマ
#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- `Script` テーブルに以下のカラムを追加:
    - `draft_date`: String (ドラフト日付)
    - `copyright`: String (著作権情報)
    - `contact`: Text (連絡先)
    - `notes`: Text (メモ)
    - `revision_text`: String (リビジョン情報)

### Alembicマイグレーション
- これらのカラムを追加するための新しいマイグレーションスクリプトを作成する。

### バックエンドロジック
#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- `parse_fountain_and_create_models` 関数内:
    - `f.metadata` 辞書にアクセスする。
    - `draft date` (または `date`), `copyright`, `contact`, `notes`, `revision` を抽出する。
    - リスト形式の値は改行で結合して文字列にする。
    - `script` オブジェクトにこれらの値を設定する。

## 検証計画

### 自動テスト
- `pytest tests/unit/test_fountain_parser.py` を実行する。
- `test_fountain_parser.py` に新しいテストケースを追加し、メタデータを含むスクリプトが正しく `Script` モデルに保存されるか確認する。

### 手動検証
- 実際にメタデータを含むFountainファイルをアップロードし、DBに保存されることを確認する（ユニットテストで十分カバー可能）。
