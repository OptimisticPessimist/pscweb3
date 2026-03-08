# 実装計画 (香盤表のキャラクターソート)

この変更は、香盤表（Scene Chart）のキャラクターの並び順を、「台本の『登場人物』欄の順番」、それがなければ「台本内の登場順」で自動ソートする機能を追加するものです。

## Proposed Changes

### Database & Models
#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
`Character`モデルに`order`カラムを追加します。
```python
    order: Mapped[int] = mapped_column(default=0)
```
その後、Alembic を使ってマイグレーションスクリプトを生成・適用します。

### Backend Services & API
#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
`parse_fountain_and_create_models` 関数内で以下を実装します。
1. `# 登場人物` 欄で定義されているキャラクター名のリストとその順番を抽出する（コロン `:` がない単なる名前の列挙でも抽出できるようにします）。
2. アクションやセリフなどでキャラクターが初登場した順番を記録する。
3. パース処理の最後に、抽出した優先順位（1. 登場人物欄の順番 -> 2. 台本登場順）に基づき、各 `Character` インスタンスの `order` に連番（1, 2...）を割り当てる。

#### [MODIFY] [scene_chart.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/scene_chart.py)
`CharacterInScene` スキーマに `order` フィールドを追加します。
```python
    order: int = Field(..., description="表示順")
```

#### [MODIFY] [scene_charts.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/scene_charts.py)
`_build_scene_chart_response` 関数内で、`CharacterInScene` オブジェクトを初期化する際に、DBの `mapping.character.order` から値を取得してセットします。

### Frontend
#### [MODIFY] [SceneChartPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scene_charts/pages/SceneChartPage.tsx)
香盤表の列定義部分で、抽出した全キャラクターを保持する `uniqueChars` のリストを生成する際、重複を排除した上で `order` フィールドによる昇順ソートを実施します。これにより、テーブルの列順が正しくなります。

### Tests
#### [MODIFY] [test_fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/tests/unit/test_fountain_parser.py)
Fountainスクリプトパース後に、`Character` モデルの `order` カラムが正しく設定されていることをテストするケースを追加・修正します。
- 登場人物欄での順序が優先されること
- 定義にない人物はセリフ登場順になること

## Verification Plan

### Automated Tests
バックエンドの pytest コマンドでユニットテストを実行し、テストが通過するか確認します。
```bash
cd backend
pytest tests/unit/test_fountain_parser.py -v
```

### Manual Verification
1. ローカル開発サーバーを起動し、フロントエンドにアクセス。
2. 以下のような内容のFountainスクリプトをアップロード：
```fountain
Title: テスト台本

# 登場人物
探偵
被害者
容疑者A
容疑者B
容疑者C
容疑者D

# 第1幕
## 第1場

@探偵
1

@被害者
2

@容疑者A
3
```
3. 香盤表タブを開き、キャラクターの列順が（探偵, 被害者, 容疑者A...）のように「登場人物」欄で指定した順番で表示されることを確認する。
