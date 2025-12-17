# タスクリスト

- [x] `/auth/login` 404エラーの調査
    - [x] `backend/src/api/auth.py` の `login` エンドポイント定義を確認
    - [x] `backend/src/main.py` のルーター登録を確認
    - [x] Azure Functionsの構成 (`function_app.py`, `host.json`) を確認
    - [x] デバッグ用エンドポイントを追加してルーティングを検証する
        - 結果: `/api/debug` で404エラー -> アプリ起動エラーと判明。
    - [x] `function_app.py` の堅牢化
        - [x] インポートエラー (`SyntaxError`) をキャッチして詳細を表示
    - [x] 原因特定と修正 (SyntaxError in `rehearsals.py`)
- [x] 問題の修正 (rehearsals.pyのコミット漏れ修正)
- [x] 修正の検証
- [x] クリーンアップ (/debug エンドポイント削除)
