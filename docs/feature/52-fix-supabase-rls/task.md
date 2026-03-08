# タスク: Supabase RLSエラーの修正

## 概要
Supabaseのデータベースリンターで検出された、`public`スキーマ内の以下のテーブルに対するRLS（Row Level Security）未有効エラーを修正する。

- `schedule_poll_candidates`
- `schedule_poll_answers`
- `schedule_polls`

## 作業内容
- [ ] Alembicマイグレーションの作成
  - 上記3つのテーブルに対してRLSを有効化する SQL を実行。
  - 既存のパターンに従い、"Enable all access" ポリシーを追加する。
- [ ] マイグレーションの実行（環境が許せば）
- [ ] 修正内容の確認

## 完了条件
- 上記3つのテーブルに対して `ENABLE ROW LEVEL SECURITY` が適用されている。
- 適切なアクセスポリシーが設定されている。
