# カレンダー日程調整・シーン判定機能 (バックエンド実装完了)

## 概要
カレンダー上での日程調整と、その日程でどのシーンが稽古可能かを自動判定する機能のバックエンド実装を完了しました。

## 変更内容

### 1. スキーマの追加 (`backend/src/schemas/schedule_poll.py`)
カレンダー表示およびシーン判定結果を返すための新しいスキーマを定義しました。
- `SceneAvailability`: 特定の日程におけるシーンの可否、リーチ判定、不足メンバー。
- `PollCandidateAnalysis`: 候補日程ごとの参加メンバー、可能シーン、リーチシーンの分析結果。
- `SchedulePollCalendarAnalysis`: 日程調整全体の分析結果。

### 2. サービス層の実装 (`backend/src/services/schedule_poll_service.py`)
シーン判定とリーチ判定（あと1人で可能）のロジックを実装しました。
- `get_calendar_analysis`:
  - 最新の脚本と香盤表（`SceneCharacterMapping`）からシーンごとの必要キャラを特定。
  - キャスティング情報から必要なユーザーを特定。
  - 各候補日程に対し、回答（OK/Maybe）に基づき「可能シーン」と「リーチシーン」を算出。
  - ダブルキャスト対応（1人でもいればOK）。

### 3. APIエンドポイントの追加 (`backend/src/api/schedule_polls.py`)
フロントエンドから分析結果を取得するためのエンドポイントを追加しました。
- `GET /projects/{project_id}/polls/{poll_id}/calendar-analysis`

## 検証結果

### 単体テスト
以下の判定ロジックを検証するテストを作成し、パスすることを確認しました。
- 全キャストが揃っている場合の `is_possible` 判定。
- 1人（1役）だけ不足している場合の `is_reach` 判定と不足メンバー名の取得。

実行コマンド:
```powershell
./backend/.venv/Scripts/python -m pytest backend/tests/unit/test_calendar_analysisv1.py
```
結果: `2 passed`

## 今後の予定
- フロントエンドでのカレンダーUI実装とAPI連携。
