# 実装計画 - 脚本のト書き（Action）対応

脚本のプレビューでト書き（Stage Directions/Action）が表示されない問題を修正します。現在は全ての行（Line）がキャラクターに紐付く必要があるため、ト書きが無視されています。

## ユーザーレビュー事項
> [!IMPORTANT]
> データベースのスキーマ変更が必要です：`Line.character_id` を Null許容（nullable）に変更します。

## 変更内容

### Backend

#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- `Line` モデルの `character_id` を Nullable に変更します。
- `character_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("characters.id"), nullable=True)`
- `character` リレーションの型ヒントを `Mapped["Character | None"]` に更新します。

#### [NEW] Migration Script
- `alembic revision --autogenerate` を使用して、`lines` テーブルの `character_id` カラムを nullable に変更するマイグレーションを作成します。

#### [MODIFY] [schemas/script.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/script.py)
- `LineResponse` モデルの `character` フィールドを Optional に変更します。
- `character: CharacterResponse | None = Field(None, description="登場人物")`
- これにより、APIレスポンスでト書き（キャラクターなし）を返却可能にします。

#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- パースループ内で `element.element_type == "Action"` のハンドリングを追加します。
- Actionの場合、`character_id=None` で `Line` オブジェクトを作成します。

#### [MODIFY] [scene_chart_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/scene_chart_generator.py)
- 香盤表生成時に `None` の `character_id` を無視するように修正します。
- `character_ids = {line.character_id for line in scene.lines if line.character_id is not None}`

### Frontend

#### [MODIFY] [index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/types/index.ts)
- `Line` インターフェース (`Script['scenes'][0]['lines'][0]`) を更新し、`character` を `null` または `optional` が許容されるようにします。

#### [MODIFY] [ScriptDetailPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/ScriptDetailPage.tsx)
- キャラクターが紐付かない行（ト書き）の描画ロジックを追加します。
- `line.character` が存在しない場合、その行をト書きとして（例：全幅、イタリック、グレー文字などで）表示します。

## 検証計画

### 自動テスト
- `tests/unit/test_fountain_parser.py` に Action 要素を含む脚本のテストケースを追加し、`character_id` が None として保存されることを検証します。
- `tests/unit/test_scene_chart_generator.py` (もしあれば) または結合テストで、ト書きがあっても香盤表が正しく生成される（エラーにならない）ことを確認します。

### 手動検証
- ト書きを含む脚本（標準Fountain形式または日本語形式）をアップロードします。
- 脚本詳細ページを確認します。
- ト書きがセリフとは区別されて表示されることを確認します。
- 香盤表ページを確認し、エラーが出ていないこと、およびト書きが余計なキャラクターとして認識されていないことを確認します。
