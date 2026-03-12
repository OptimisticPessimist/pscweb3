# あらすじ表示不備の修正実装計画

あらすじセクションにおいて、テキストが欠落したり、特定の要素（キャラクター名、セリフ、括弧書き）が表示されない問題を修正します。また、前処理ロジックの副作用によりキャラクター名が正しく認識されなくなっていた問題を解消します。

## Proposed Changes

### backend

#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- `Scene #0` (Synopsis) の処理時、`Action` や `Synopsis` 要素以外に `Character`, `Dialogue`, `Parenthetical` 要素が来ても `description` に追加するようにロジックを強化します。
- `Parenthetical` 要素の保存時に、意図しない空白が含まれないよう `strip()` を適用します。
- 動作追跡のためのデバッグログを追加します。

#### [MODIFY] [fountain_utils.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/utils/fountain_utils.py)
- `preprocess_fountain` において、すべての行に強制的に `!` (Action修飾子) を付与するのをやめ、全大文字の行（キャラクター名の可能性が高い行）はそのまま保持するように修正します。これにより、パーサーがキャラクター要素を正しく識別できるようになります。

## Verification Plan

### Automated Tests
- `python repro_synopsis.py` を実行し、あらすじセクションの内容がすべて `Scene #0` の `description` に含まれていることを確認します。
- `pytest backend/tests/unit/test_fountain_preservation.py` を実行し、既存の保存機能にデグレが発生していないことを確認します。

### Manual Verification
- スクリプトビューアーで、あらすじが欠落なく表示されることを視覚的に確認します。
