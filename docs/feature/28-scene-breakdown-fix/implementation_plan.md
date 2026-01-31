# [香盤表（Scene Breakdown）の修正]

## 現状の課題
- 香盤表（Scene Breakdown）に「登場人物」しか表示されない。
- 理由：DBの `scenes.description` カラム（シーンの概要/ト書き）がFountainパース時に空のままになっているため。

## Proposed Changes
### Backend
#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- `Scene` モデル作成時に `description` を埋めるロジックを追加する。
- **ロジック概要**:
    - Scene Heading の直後にある `Action` (ト書き) を収集する。
    - `Character` や `Dialogue` が現れるまでの間のト書きを結合して `Scene.description` に格納する。
    - フラグ `collecting_description` を用意し、シーン開始時にTrue、キャラ/セリフ検出時にFalseにする。
    - 取得したト書きは `\n` で結合して保存。

## Verification Plan
- `test_scene_description.py` (既存/修正) を実行し、`Scene.description` に値が入ることを確認。
