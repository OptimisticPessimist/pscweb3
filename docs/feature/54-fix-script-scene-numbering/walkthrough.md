# 修正内容の確認

## 概要
Fountainパーサーにおいて、`# 登場人物` や `## 登場人物` といった見出しに、シーンキーワードである「場（ば / じょう）」が含まれているため、誤ってシーン1としてカウントされてしまうバグを修正しました。

## 変更内容
### バックエンド
- **`backend/src/services/fountain_parser.py`**
  - シーンキーワード判定（`has_scene_keyword`）直後に、見出しテキスト（`content_stripped`）に `登場人物` または `Character` が含まれている場合は `has_scene_keyword = False` となるように条件を追加しました。
  - 同様に、`is_section_scene` および `is_valid_scene_heading` の判定後にも、`登場人物` または `Character` が含まれている場合は強制的に False にする安全装置を設けました。

### テスト
- **`backend/tests/unit/test_fountain_parser.py`**
  - 新たなテストケース `test_parse_fountain_with_character_section_scene_numbering` を追加。
  - `# 登場人物` ブロックが無視され、その後の `## 第1場` が正しくシーン1 (Scene #1) としてパースされることをアサートしました。

## 検証結果
- `pytest backend/tests/unit/test_fountain_parser.py` により、対象ロジックが正しく機能することを単体テストとして確認しました。
- 統合テストコマンド `pytest backend/tests/` を実施し、デグレ(Regression)が発生していないことを確認しました。
