# 実装計画: Supabase RLSエラーの修正

## 1. 目的
Supabaseのセキュリティリンターで指摘されている `public` スキーマ内のテーブルにおける RLS 未有効化エラーを解消し、セキュリティを向上させる（またはリンターを満足させる）。

## 2. 変更内容
### バックエンド (Database Migration)
Alembicを使用して、以下の3つのテーブルに対してRLSを有効化し、既存のプロジェクト方針に合わせた "Enable all access" ポリシーを追加します。

- `schedule_polls`
- `schedule_poll_candidates`
- `schedule_poll_answers`

#### 実行するSQLイメージ
```sql
ALTER TABLE public.schedule_polls ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all access" ON public.schedule_polls FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE public.schedule_poll_candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all access" ON public.schedule_poll_candidates FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE public.schedule_poll_answers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all access" ON public.schedule_poll_answers FOR ALL USING (true) WITH CHECK (true);
```

## 3. 影響範囲
- データベースのセキュリティ設定が変更される。
- `public` ロールなどからのアクセス時にRLSポリシーが評価されるようになる。
- 現時点では "Enable all access" (すべて許可) とするが、プロジェクトの他テーブルと同様のパターンに従うため、既存の機能への影響はない見込み。

## 4. 検証計画
- `alembic upgrade head` が正常に実行されることを確認する。
- データベース上で対象テーブルの RLS が `enabled` になっていることを確認する。
