# データ不整合の修正 (Project Public Status)

## 問題
- デプロイ後、既存の「公開スクリプトを持つプロジェクト」が `is_public=False` (デフォルト値) のままになっている。
- これにより、全プロジェクトが「非公開」としてカウントされ、作成上限(2つ)に達していると判定されている。

## タスク
- [x] `backend/fix_data_is_public.py` の作成
  - 全プロジェクトをループ
  - 公開脚本(`is_public=True`)を持っているかチェック
  - 持っていれば `TheaterProject.is_public = True` に更新
- [x] スクリプトの実行 (ログにて成功確認)
- [x] 動作確認（ユーザー依頼）
