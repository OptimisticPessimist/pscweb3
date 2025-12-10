# Phase 3 & 4: リファクタリングとタイムゾーン対応

## Phase 3: リファクタリング
- [x] Phase 3-1: 権限チェック共通化 (`get_script_member_dep`)
- [x] Phase 3-2: upload_script分割 (`services/script_service.py`)

## Phase 4: タイムゾーン問題の解決
- [x] `db/models.py` の `DateTime` 型確認
- [x] APIおよびService層でのTimezone Aware -> Naive変換の実装

---

## Phase 6: UI改善と機能追加

### 1. 稽古作成時の出欠確認機能
- [x] `types/index.ts` の `RehearsalCreate` 型定義更新
- [x] `RehearsalModal.tsx` に出欠確認チェックボックスとdeadline入力欄を追加
- [x] バックエンドへの送信データ対応

### 2. リマインダー機能
- [x] `AttendanceService` リマインダー実装
- [x] UIボタン設置

## Phase 7: 稽古データ構造の改善 (複数シーン・参加者管理)

### 1. データベース・APIの変更
- [x] Model: `Rehearsal` と `Scene` の多対多リレーション追加
- [x] API: `add_rehearsal` ロジック改修（複数シーン、参加者明示保存）
- [x] Fix: `MissingGreenlet` エラー回避（中間テーブル直接操作）
- [x] Fix: `RehearsalSchedule` の `created_at` 制約エラー対応

### 2. Frontend UIの変更
- [x] `RehearsalModal`: 複数シーン選択対応
- [x] `RehearsalModal`: 参加者（キャスト・スタッフ）の自動選択・手動編集UI
- [x] Refactor: `useRehearsalParticipants` フックへのロジック分離
- [x] Type: `any` キャストの排除

## Phase 8: Testing
- [x] Backend Integration Test (`test_rehearsals.py`)
- [x] Frontend UI Test (`RehearsalModal.test.tsx`)

---

## 現在の進捗
Phase 3-8 完了。検証済み。
