# あらすじ表示不備の修正計画

あらすじ（シーン番号0）において、ト書き以外の要素（セリフや括弧書きなど）が挟まると、その後のト書きがシーンの概要（`description`）として蓄積されない問題を修正します。

## 現状の課題
`fountain_parser.py` において、`collecting_description` フラグが以下の条件で `False` になります：
- 登場人物（`Character`）要素が出現した時
- セリフ（`Dialogue`）要素が出現した時
- `Action` または `Synopsis` 以外の要素が出現した時
- 一行セリフ（`@Name Dialogue`）が出現した時

あらすじシーンではセリフや括弧書きが含まれることがありますが、これらが出現した時点で概要の収集が止まってしまうため、後続のト書きが表示されなくなっています。

## 修正内容

### [Component] Backend (Parser)

#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- **あらすじシーン（シーン0）における収集ロジックの変更**:
    - 通常のシーンでは、冒頭のト書きのみを `description` とし、対話が始まったら収集を止めます（従来の挙動を維持）。
    - **あらすじシーン（シーン0）に限り**、要素のタイプに関わらず、そのシーン内の全ト書き（`Action` または `Synopsis` 要素）を `description` に蓄積し続けるように変更します。
    - `collecting_description` のリセット条件に `and current_scene.scene_number != 0` を追加します。

## 検証プラン

### 自動テスト
- `backend/tests/unit/test_fountain_parser.py`（存在すれば）または新規テストを作成し、セリフを挟んだ複数行のト書きがあらすじの `description` に含まれることを確認します。

### 手動確認
1. 以下のような構造のFountainファイルをアップロードします：
   ```fountain
   # あらすじ
   ト書き1
   @キャラ
   セリフ
   ト書き2
   ```
2. 脚本ビューアーで「あらすじ」セクションに「ト書き1」と「ト書き2」の両方が表示されることを確認します。
