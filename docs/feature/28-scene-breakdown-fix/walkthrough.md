# Walkthrough - Scene Breakdown Fix

香盤表（Scene Breakdown）にシーンの概要（ト書き）が表示されるように修正しました。

## Changes

### 1. シーン説明の自動抽出
- `fountain_parser.py` を修正し、シーンヘッダーの直後に書かれたト書き（Action）を収集して `Scene.description` に保存するようにしました。
- 登場人物（Character）やセリフ（Dialogue）が現れた時点で説明の収集を終了します。

#### Before
- 香盤表にはシーン番号と登場人物のみが表示され、シーンの内容が不明だった。

#### After
- シーン冒頭のト書きが香盤表の「概要」欄などに表示されるようになります（DBには保存されているため、フロントエンド等の表示側が対応していれば即座に反映されます）。

## Verification
- テストスクリプトを作成し、Fountainパース時に `Scene.description` が正しく格納されることを確認しました。
