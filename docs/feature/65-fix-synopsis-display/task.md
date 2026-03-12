# タスクリスト - あらすじ表示の修正

- [x] 現状の課題の特定と再現スクリプト (`repro_synopsis.py`) の作成
- [x] `backend/src/utils/fountain_utils.py` の修正
  - [x] あらすじセクション内での強制 `=` プレフィックス付与の削除
- [x] `backend/src/services/fountain_parser.py` の修正
  - [x] シーン#0 における全要素（Character, Dialogue, Action, Parenthetical 等）の説明文への集約ロジックの実装
  - [x] セリフの整形（"名前: セリフ"）
  - [x] シーン#0 でのキャラクター名単体追加のスキップ（重複防止）
  - [x] 不要なデバッグプリントの削除
- [x] 再現スクリプトによる動作確認
- [x] `docs/feature/65-fix-synopsis-display/` へのドキュメント作成
- [x] プルリクエストの作成とマージ
