# 実装計画 - プロジェクト制限修正 & UI改善

## 目的
制限内であるにもかかわらず新規プロジェクトが作成できない問題を修正し、ダッシュボード上で公開プロジェクトを視覚的に区別できるようにする。

## 変更案

### Backend
#### アーキテクチャの変更 (推奨)
長期的な保守性とパフォーマンスを考慮し、**`TheaterProject` テーブルに `is_public` カラムを明示的に追加**することを提案します。
現状の「公開脚本が含まれているか毎回計算する」方式は計算コストが高く、作成時のロジックも複雑になりがちです。

**設計方針:**
1. **DBスキーマ**: `theater_projects` テーブルに `is_public` (Boolean, default=False) を追加。
2. **プロジェクト作成時**:
   - 通常作成: `is_public = False`
   - 公開脚本インポート時: `is_public = True` で作成
3. **状態の同期**:
   - 脚本アップロード/更新時: 脚本が公開設定なら、親プロジェクトの `is_public` を `True` に更新。
   - 脚本削除/非公開化時: プロジェクト内の公開脚本が0になったら、`is_public` を `False` に戻す（オプション、あるいは一度公開したら公開のままとするか要検討）。
   - **今回はシンプルに**: 「公開脚本が1つでもあればプロジェクトは公開」というルールに基づき、脚本操作時にフラグを更新するロジックを実装します。

#### `src/services/project_limit.py`
- ロジックを大幅に簡素化。
- `SELECT COUNT(*) FROM theater_projects WHERE user_id = ? AND is_public = FALSE` だけで判定可能になります。

#### `src/api/projects.py` / `src/services/project_service.py`
- プロジェクト作成API (`create_project`) に `is_public` 引数を追加（内部利用のみ、または管理者用）。
- インポート処理ではこのフラグを立ててプロジェクトを作成します。

#### `src/services/script_processor.py`
- 脚本保存時に `project.is_public` を再評価して更新する処理を追加。

### Frontend
#### `src/features/dashboard/pages/DashboardPage.tsx`
- プロジェクトオブジェクトの `is_public` プロパティを直接参照してUIを切り替え可能。シンプルになります。


## 検証計画
- プロジェクト作成制限の手動検証
  - 通常作成時の制限（非公開2つまで）
  - 公開脚本インポート時の制限除外
- ダッシュボードでのUI確認
  - 公開プロジェクトの表示（アイコン/バッジ等）
