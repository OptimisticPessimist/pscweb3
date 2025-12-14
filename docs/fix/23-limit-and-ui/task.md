# プロジェクト制限の修正とダッシュボードUI改善

## 問題点
1. **プロジェクト制限のバグ**: 制限（公開: 無制限、非公開: 2つ）を守っていても、新規プロジェクトが作成できない場合がある。
   - 期待値: 公開プロジェクトは制限対象外。非公開プロジェクトの上限のみ2つ。
2. **ダッシュボードUI**: 公開プロジェクトと非公開プロジェクトの視覚的な区別がない。
3. **公開脚本のインポート**: プロジェクト作成に失敗する（制限バグが原因の可能性が高い）。

## タスク
- [x] プロジェクト制限ロジックの分析と修正 <!-- id: 0 -->
  - [x] `src/services/project_limit.py` の確認
  - [x] `is_public` 判定ロジックの検証
  - [x] 「公開脚本のインポート」フローの確認
- [x] DBスキーマ変更とロジック実装
  - [x] `TheaterProject` モデルに `is_public` 追加
  - [x] マイグレーション実行
  - [x] Verify Project Deletion Code (Backend & Frontend routes align)
- [x] Fix 500 Error on key constraint (AttendanceEvent cascade)
- [x] Verify Frontend Build (fixed unused variable)
- [x] Push to main
- [x] User Deployment & Verification
- [x] Public Script Enhancements <!-- id: 3 -->
  - [x] Frontend Layout: Wrap public routes in AppLayout
  - [x] Backend: Add `source_public_script_id` to `ProjectCreate`
  - [x] Backend: Logic to copy script in `create_project`
  - [x] Frontend: Update `DashboardPage.tsx` to handle import state
  - [x] Frontend: Add "Create Project" button on Public Script detail
- [x] Restriction: Prevent imported scripts from being made public <!-- id: 4 -->
  - [x] Frontend: Disable is_public checkbox when importing
  - [x] Backend: Force is_public=False when source_script is present
- [x] Fix 500 Error: Backend import error (ScriptProcessor not found) <!-- id: 5 -->
- [x] Fix Missing Public Badge: Include `is_public` in `list_projects` response <!-- id: 6 -->
- [x] UI Improvement: Display Invitation Usage Count <!-- id: 7 -->
  - [x] `project_limit.py` 更新
  - [x] `script_processor.py` (同期ロジック) 更新
  - [x] `api/projects.py` 更新
- [x] ダッシュボードUIの改善 <!-- id: 1 -->
  - [x] Dashboard APIで脚本の公開ステータスを取得できるようにする
  - [x] `DashboardPage.tsx` を更新し、公開プロジェクトにラベルや色を付ける
- [x] 修正の検証 <!-- id: 2 -->
  - [x] 公開1/非公開1の状態で新規プロジェクト作成をテスト
  - [x] 公開脚本のインポートをテスト
