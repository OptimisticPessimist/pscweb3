# プロジェクト作成数制限 実装計画

## Goal Description
ユーザーが所有できるプロジェクト数を2つに制限します。これにより、リソースの乱用を防ぎつつ、一定の柔軟性を確保します。

## User Review Required
- 特になし

## Proposed Changes

### Backend
#### [MODIFY] [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
- `create_project` APIにおいて、現在のユーザーが既に `owner` ロールを持つプロジェクトのメンバーであるかをチェックするロジックを追加します。
- 既にオーナーであるプロジェクトが2つ以上存在する場合、HTTP 400エラー ("You can only own up to 2 projects.") を返します（エラーメッセージは英語）。

### Frontend
#### [MODIFY] [DashboardPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/dashboard/DashboardPage.tsx)
- `projects` データから現在のユーザーが `owner` であるプロジェクトの数をカウントします。
- カウントが2以上の場合、"Create Project" ボタン（ヘッダー部分および空の状態のボタン両方）を `disabled` に設定します。
- ボタンが `disabled` の場合、ユーザーに理由（翻訳キー: `dashboard.projectLimitReached` 等）を伝えるツールチップまたはテキストを表示する等のUI改善を行います。
- `src/locales/{ja,en,ko,zh-CN,zh-TW}/translation.json` に翻訳キーを追加します。

## Verification Plan

### Manual Verification
1. 既にプロジェクトを2つ所有しているユーザーでログインし、新しいプロジェクトを作成しようとする -> エラーになることを確認。
2. プロジェクトを1つ所有しているユーザーでログインし、新しいプロジェクトを作成しようとする -> 成功することを確認。
3. プロジェクトのメンバー（オーナーではない）であるユーザーでログインし、新しいプロジェクトを作成しようとする -> 成功することを確認。
