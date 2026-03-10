# 実装計画: 脚本あらすじ欠落の修正

## 1. 現状の課題
現在、Fountain形式の脚本をアップロードした際、以下の要素がDBに保存されず、表示から消えてしまう問題があります。
- `=` で始まる「あらすじ（Synopsis）」要素
- `()` で囲まれた「括弧書き（Parenthetical）」要素
- `>` で始まる「移行（Transition）」要素
- `> <` で囲まれた「中央揃え（Centered Text）」要素

また、シーンの先頭にあるト書き（Action）を `Scene.description` に収集するロジックに不備があり、最初の1行しか保存されない（あるいは保存されない）状態になっています。

## 2. 修正方針
`backend/src/services/fountain_parser.py` を修正し、以下の改善を行います。

1. **要素タイプの拡充**:
   - `python-fountain` パルサーが返す `Synopsis`, `Parenthetical`, `Transition`, `Centered Text` 要素を処理対象に含め、これらを脚本の「行（Line）」としてDBに保存するようにします。
2. **収集ロジックの改善**:
   - シーン冒頭の `Synopsis` や `Action` 要素を、セリフや次のシーンが現れるまで `Scene.description` に累積して保存するようにします。
3. **マーカーの除去**:
   - `=` や `!` などの Fountain 特有のマーカーを、表示用のテキストからは適切に除去します。

## 3. 具体的な修正箇所

### `backend/src/services/fountain_parser.py`
- `parse_fountain_and_create_models` 関数内のメインループを修正。
- `elif element.element_type == "Action":` の部分を、他の要素タイプも含むように拡張。
- `collecting_description` のフラグ管理を修正し、複数のAction/Synopsisを連結できるようにします。

## 4. 期待される効果
- 脚本内のあらすじ（`=` で始まる行）がすべて表示されるようになります。
- 括弧書きや移行などの演出指示が正しく表示されるようになります。
- シーンの冒頭説明が `description` フィールドにも正しく格納されるようになります。
