# 日程調整カレンダー シーン絞り込み機能 バグ修正（選択肢が出ない問題の再修正）

## 課題
- シーン絞り込みのドロップダウンリストに `schedulePoll.allScenes` しか出ない（シーンが一つも表示されない）。

## 原因分析
- 現在のフロントエンドでの「シーン一覧」の生成ロジックは、APIレスポンスの `analyses`（各候補日程の分析結果）内にある `possible_scenes` と `reach_scenes` をマージして一意のシーンリストを作成しています。
- つまり、**どの候補日程においても「稽古可能」または「リーチ状態」にならないシーン（例えば役者が全く足りない等の理由で完全に不可能なシーン）は、プルダウンの選択肢に登場しません。**
- すべての候補日で全くシーンが成立しない場合、選択肢は空になってしまいます。ユーザーは、すべてのシーンからフィルタリングして「どの候補日ならこのシーンが可能か」を確認したいはずなので、この挙動は不適切です。

## Proposed Changes

### Backend
1. **[MODIFY] `backend/src/schemas/schedule_poll.py`**(file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/schedule_poll.py)
   - `SchedulePollCalendarAnalysis` スキーマに `all_scenes: list[PollSceneInfo] = []` を追加。
   - 新規に `PollSceneInfo` スキーマを定義。

2. **[MODIFY] `backend/src/services/schedule_poll_service.py`**(file:///f:/src/PythonProject/pscweb3-1/backend/src/services/schedule_poll_service.py)
   - `get_calendar_analysis` メソッドで、スクリプトに紐づくすべてのシーン情報（`id`, `scene_number`, `heading`）を `all_scenes` としてレスポンスに含めるように修正。

### Frontend
3. **[MODIFY] `frontend/src/features/schedule_polls/api/schedulePoll.ts`**(file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule_polls/api/schedulePoll.ts)
   - `SchedulePollCalendarAnalysis` インターフェースに `all_scenes: PollSceneInfo[]` を追加。
   - `PollSceneInfo` インターフェースを追加。

4. **[MODIFY] `frontend/src/features/schedule_polls/components/SchedulePollCalendar.tsx`**(file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule_polls/components/SchedulePollCalendar.tsx)
   - `useMemo` で作成している `scenes` 変数を、`analysis.all_scenes` があればそれを最優先で利用するように修正。

## Verification Plan
1. バックエンドの `SchedulePollCalendarAnalysis` のスキーマ更新とサービスの実装を修正後、ローカルでフロントエンドを立ち上げる。
2. どの候補日にも「可能」「リーチ」判定が出ていないシーンであっても、プルダウンリストに正しく表示されることを確認する。
3. プルダウンのすべてのシーン名が正しく並んでいることを確認する。
