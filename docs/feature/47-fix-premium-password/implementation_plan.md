# 実装計画: プレミアムパスワードの効果がないバグの修正

## 1. 目的
プレミアムパスワード（特に "test" ティア等）を入力してもプロジェクト作成数制限を超えられない不具合を修正する。

## 2. 修正方針
1. **空白の考慮と型の安全性の強化 (`backend/src/services/project_limit.py`)**
   - パスワード比較時に前後の空白を取り除く(`strip()`)。
   - `limit` (環境変数やJSON経由でStringになっている可能性がある) を `int` に安全にキャストする。
2. **パスワードによるティア取得の強化 (`backend/src/services/premium_config.py`)**
   - パスワードによるティア判定時にも `strip()` を適用する。
3. **Azure Blob Storageから取得した設定値のデフォルトマージ (`backend/src/services/premium_config.py`)**
   - `refresh_config` で blob から JSON を読み込んだ際に、既存データに「後から追加されたティア（例: test）」が含まれていない場合、`_get_default_config()` の値で補完する。

## 3. レビューポイント
- 既存のプロジェクト作成動作や通常の上限判定に悪影響を与えないこと。
- パスワードなしのユーザーに対して安全にデフォルト値（上限1つ）が適用されること。
