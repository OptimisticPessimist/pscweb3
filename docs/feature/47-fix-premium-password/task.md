# プレミアムパスワードの効果がないバグの修正

## 概要
プレミアムパスワードを入力しても、プロジェクト作成数の上限を超えて新規プロジェクトが作成できないバグを修正する。
原因として、Azure BlobからJSONを取得する際に新しく追加された `test` 階層が存在しない場合や、型の不一致(`str` 対 `int`)、パスワード末尾の余計な空白などが考えられる。

## タスク内容

- [x] バグの調査・再現
  - [x] テストスクリプトを作成し挙動を検証
- [x] 実装の修正
  - [x] `project_limit.py` にて、パスワードの前後の空白削除および上限数(`limit`)の型変換処理を追加
  - [x] `premium_config.py` の `get_tier_by_password` にて空白削除処理を追加
  - [x] `premium_config.py` の `refresh_config` 処理にて、取得したJSONとデフォルト設定をマージするよう変更し、`test` 階層の欠落を防ぐ
- [x] テスト実行・確認
- [x] ドキュメント作成
  - [x] task.md
  - [x] implementation_plan.md
  - [x] walkthrough.md
- [ ] コミット・マージ
