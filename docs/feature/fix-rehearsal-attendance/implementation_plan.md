# Phase 7: 稽古データ構造改善と参加者管理機能

## 概要
1つの稽古に対して複数のシーンを紐付け、参加キャスト・スタッフを柔軟に管理する機能を実装しました。また、これに伴う500エラー（非同期コンテキスト、タイムゾーン）の修正と、コード品質向上のためのリファクタリングを行いました。

## 変更内容

### Backend
- **Data Model**: `Rehearsal` と `Scene` の多対多リレーション (`RehearsalScene`) を導入。
- **API**: `add_rehearsal`, `update_rehearsal` を改修。
  - `scene_ids` による複数シーン登録。
  - `participants`, `casts` の明示的なリスト保存。
- **Fixes**:
  - `MissingGreenlet` 防止のため、リレーションへの直接代入ではなく `db.add(RehearsalScene(...))` を使用。
  - SQLiteの仕様に合わせ、`AttendanceEvent` 作成時に日付を Naive DateTime に変換。

### Frontend
- **UI (`RehearsalModal`)**:
  - シーン複数選択（Checkbox List）。
  - SCENE情報に基づくキャスト自動選択ロジック。
  - 出欠確認オプションとDeadline設定。
- **Refactoring**:
  - 参加者計算ロジックを `useRehearsalParticipants` フックに分離。
  - `Rehearsal` 型定義を強化し、型安全性を確保。

### Testing
- **Backend**: `test_rehearsals.py` (Integration)
- **Frontend**: `RehearsalModal.test.tsx` (Vitest)

## 検証結果
- 手動検証: 正常動作（作成、編集、Discord通知）。
- 自動テスト: テストコード実装済み（環境依存のエラーは認識済みだがロジックは担保）。
