# 実装計画 - 個人スケジュール一覧

## ゴールの説明
キャストやスタッフが、個々のプロジェクトを確認して回ることなく、自分が参加している全プロジェクトの稽古スケジュールおよび **マイルストーン（本番日程など）** を一箇所で確認できるようにする。

## ユーザーレビュー事項
- **UIデザイン**: 将来的には **カレンダー表示** を目指すが、今回のMVPでは **日付順のリスト表示** を採用する。
- **スコープ**: 「稽古」だけでなく **「プロジェクトのマイルストーン（本番など）」も含めて表示する**。

## 変更内容

### バックエンド
#### [NEW] [backend/src/db/models.py]
- **`Milestone` モデルの追加**
    - `id`, `project_id`, `title`, `date`, `description`, `color` (任意)
    - `TheaterProject` とのリレーション（Cascade削除対応）

#### [MODIFY] [backend/src/api/users.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/users.py)
- `GET /users/me/schedule` エンドポイントを追加。
- 以下の2つのソースからデータを収集・統合して日時順にソートする：
    1. **稽古 (Rehearsals)**: 自身が `RehearsalParticipant` または `RehearsalCast` として関連付けられているもの。
    2. **マイルストーン (Milestones)**: 自身が所属するプロジェクト（`ProjectMember`）の全マイルストーン。
- レスポンス構造:
    ```json
    [
      { "type": "rehearsal", "date": "...", "project": "...", "title": "シーン稽古", "role": "役名A" },
      { "type": "milestone", "date": "...", "project": "...", "title": "本番初日", "description": "..." }
    ]
    ```

#### [MODIFY] [backend/src/api/projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
- マイルストーン管理用エンドポイントを追加（プロジェクト設定画面等で使う想定だが、まずはデータ作成のため）。
    - `POST /projects/{project_id}/milestones`
    - `GET /projects/{project_id}/milestones`
    - `DELETE /projects/{project_id}/milestones/{milestone_id}`

### フロントエンド
#### [NEW] [frontend/src/features/schedule/MySchedulePage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule/MySchedulePage.tsx)
- スケジュール一覧ページ。
- ユニオン型（Rehearsal | Milestone）のリストを日付順にレンダリング。
- マイルストーンは視覚的に区別（例: 背景色を変える、アイコンを変える）。

#### [MODIFY] [frontend/src/features/dashboard/api/dashboard.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/dashboard/api/dashboard.ts)
- `getMySchedule` 関数を追加。

## 検証計画
### 自動テスト
- `GET /users/me/schedule` が稽古とマイルストーンを混在させて日付順に返すかテスト。
- 他のプロジェクトのマイルストーンが見えないことを確認。

### 手動検証
1. プロジェクト設定で「本番日」マイルストーンを作成。
2. 稽古をいくつか作成。
3. 「マイスケジュール」を開き、本番日と稽古が時系列に並んでいることを確認。
