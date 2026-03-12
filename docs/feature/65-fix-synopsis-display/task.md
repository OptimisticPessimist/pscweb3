# あらすじ表示不備の修正タスク

- [x] 現象の再現と原因特定 (Scene #0 における要素収集漏れの確認)
- [/] Fountainパーサー (`fountain_parser.py`) の修正
    - [x] Scene #0 で登場人物、セリフ、括弧書きを `description` に追加するロジックの実装
    - [x] 括弧書き (`Parenthetical`) の保存内容から不要な空白を削除
- [/] 前処理ロジック (`fountain_utils.py`) の修正
    - [x] 全大文字の行（キャラクター名候補）に強制的に `!` を付与しないように調整
- [ ] 修正内容の検証
    - [ ] 再現スクリプト (`repro_synopsis.py`) の実行確認
    - [ ] 単体テスト (`test_fountain_preservation.py`) の実行確認
- [ ] ドキュメント作成
    - [x] `task.md` の作成
    - [x] `implementation_plan.md` の作成
    - [ ] `walkthrough.md` の作成
- [ ] コードレビューとマージ
