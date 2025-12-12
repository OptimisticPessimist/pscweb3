# 実装計画: キャラクターハイライトと紹介文表示

## ゴール
1. **キャラクター別セリフハイライト**: 登場人物リストをクリックすると、そのキャラクターのセリフがハイライト表示される。
2. **登場人物の紹介表示**: `# 登場人物` ブロックを解析し、紹介文を表示する。

## 変更内容

### Backend
#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- `Character` モデルに `description` (Text, nullable=True) カラムを追加。

#### [NEW] Migration Script
- Alembic マイグレーションスクリプトを作成 (`add_description_to_characters`)。

#### [MODIFY] [schemas/script.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/script.py)
- `CharacterResponse` スキーマに `description` フィールドを追加。

#### [MODIFY] [services/fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- `parse_fountain_and_create_models` 関数を修正。
- `Section Heading` 要素で `登場人物` または `Characters` を検出した場合、その後の `Action` 要素を解析。
- `Name: Description` 形式のマッチングを行い、DBに保存。

### Frontend
#### [MODIFY] [ScriptDetailPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/ScriptDetailPage.tsx)
- **State追加**: `selectedCharacterId` (string | null)。
- **ハイライト機能**:
    - キャラクターカードをクリック可能にする。
    - 選択状態でカードのデザイン変更 (border色強調)。
    - スクリプト本文の `Line` 表示部分で、`line.character.id === selectedCharacterId` の場合に `bg-yellow-100` 等を適用。
- **紹介文表示**:
    - キャラクターカード内に `character.description` があれば表示する。

## 検証計画
### 自動テスト
- `tests/unit/test_fountain_parser.py`: `# 登場人物` ブロックのパーステストを追加。

### 手動検証
1. `# 登場人物` を含んだ新しい .fountain ファイルをアップロード。
2. 詳細画面で紹介文が表示されていること。
3. クリックでハイライトが変わること。
