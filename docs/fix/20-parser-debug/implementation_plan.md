# Fountainパーサー修正計画

## 概要
`example.fountain` のような、`@キャラクター` 行の後に改行してセリフが続く形式が正しくパースされない問題を修正する。

## 問題点
現在のパーサーの前処理（pre-process）ロジックでは、`@キャラクター` の行を検出した際、その行が一行セリフ（`@Char Dialogue`）でない場合、次の行がセリフであると期待して `is_following_char = True` フラグを立てる。
しかし、その後の処理で、次の行（セリフ）がインデントされていない場合、`is_following_char` フラグが解除され、単なる `Action` として扱われてしまっている可能性がある。

## 修正案
`backend/src/services/fountain_parser.py` の前処理ロジックを見直す。

### 具体的な変更点
1. `@キャラクター` の行を処理した後、`is_following_char = True` となった場合、次の行（空白でない行）は強制的にセリフ（Dialogue）として扱うべきである。
2. 現在のロジックでは `else` ブロック（インデントされていない行）で `is_following_char = False` にしてしまっている。
3. これを、`if is_following_char: processed_lines.append(line); is_following_char = False` （セリフとして処理）とするように変更する。

## 検証計画
### 自動テスト
- `backend/debug_fountain_elements.py` を用いて、修正後のロジックで `Dialogue` 要素としてパースされることを確認する。
- 既存のテスト `backend/tests/unit/test_fountain_parser.py` が通ることを確認する。

### 手動検証
- 修正後のパーサーで `example.fountain` の内容が正しくDBに保存されるか確認する（必要であれば）。
