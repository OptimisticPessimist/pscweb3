# Walkthrough - Implement Rehearsal Participant Management & Fixes

## Overview
稽古作成・編集機能 (`RehearsalModal`) を強化し、複数シーン紐付けと参加者自動管理を実装しました。また、タイムゾーン問題や500エラーの修正、リファクタリングを実施しました。

## Changes

### 1. Feature: Participant Management
- **Backend**: `Rehearsal` と `Scene` の多対多リレーション、`participants`/`casts` の明示的保存ロジック実装。
- **Frontend**: `RehearsalModal` での複数シーン選択、参加者自動チェック（Auto-Suggest）、手動オーバーライド機能。

### 2. Bug Fixes
- **500 Error (MissingGreenlet)**: `api/rehearsals.py` でのリレーション直接代入を廃止し、`RehearsalScene` 中間テーブルへの明示的挿入に変更。
- **500 Error (DataError/Timezone)**: `AttendanceService` 呼び出し時に、Timezone Awareな日時をNaive DateTimeに変換して SQLite の制約に適合。
- **Discord Interaction**: エンドポイントURL設定の不備を修正。

### 3. Refactoring
- **Custom Hook**: `useRehearsalParticipants` を作成し、参加者計算ロジックを分離。可読性と保守性を向上。
- **Type Safety**: `Rehearsal` 型定義に `scenes` を追加し、`any` キャストを排除。

### 4. Testing
- **Backend Integration**: `tests/integration/api/test_rehearsals.py` (稽古作成・出欠イベント)。
- **Frontend Unit**: `RehearsalModal.test.tsx` (UIレンダリング・フォーム送信)。

## Verification Results
- [x] 稽古作成（複数シーン） -> 成功
- [x] 参加者自動選択 -> 成功
- [x] 出欠確認イベント作成（Discord通知） -> 成功
- [x] 編集・更新動作 -> 成功

## Next Steps
- 本番環境（Azure）へのデプロイ
