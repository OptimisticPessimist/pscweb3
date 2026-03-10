# 日程調整などのDiscord期限表示対応プラン

## 目的
日程調整やその他の期限を持つ通知をDiscordに送信する際、Discordのタイムスタンプフォーマット表示 (`<t:UNIX_TIMESTAMP:f>`) を使用し、各ユーザーのローカル（システム）時刻に合わせた期限表示を行うこと。

## 現状の調査結果（該当メッセージ・対象箇所）

現状、Discordへ送信されるメッセージのうち、期限（締切）を持つ機能は以下の2つです。

1. **出欠確認（Attendance）機能**
   - 既に `<t:timestamp:f>` を使用してDiscordのタイムゾーン自動変換処理が適用されています。
2. **日程調整（Schedule Poll）機能**
   - `SchedulePoll` モデルに `deadline`（締切）が存在しますが、現状Discordへの新規作成通知・リマインド通知の**どちらにも締切日時が含まれていません**。今回の主要な改修対象となります。

## システムが送信するメッセージの一覧と改修内容

### 1. 日程調整の新規作成時 (`backend/src/services/schedule_poll_service.py` の `create_poll`)
**【改修内容】**
現在、`title` と `description` のみが表示されています。`deadline`（締切）が設定されている場合は、文章内にDiscordのタイムスタンプタグを活用して期限を追記します。

**【送信されるメッセージイメージ（改修後）】**
```
@mention

**【日程調整】〇〇の稽古日程について**
（説明文がここに表示されます）

**回答期限:** 2023/10/31 23:59  ← ★ここを追加: `<t:{timestamp}:f>`

（※以下のボタンから回答するか、Webフォームを開いて回答してください）...
```

### 2. 日程調整のリマインド送信時 (`backend/src/services/schedule_poll_service.py` の `send_reminder`)
**【改修内容】**
現在、「〇〇の回答がまだの方がいらっしゃいます。お手数ですが回答をお願いします！」とだけ送信されています。ここに、対象の `SchedulePoll` の回答期限を追記します。

**【送信されるメッセージイメージ（改修後）】**
```
🔔 **【日程調整リマインド】**
「**〇〇の稽古日程について**」の回答がまだの方がいらっしゃいます。お手数ですが回答をお願いします！

**回答期限:** 2023/10/31 23:59  ← ★ここを追加: `<t:{timestamp}:f>`

@mention @mention ...
```

### 3. 出欠確認のリマインド送信時 (`backend/src/services/attendance_tasks.py` の `_send_reminder`)
**【改修内容】**
既存のコードで `deadline_str = f"<t:{deadline_ts}:f> (<t:{deadline_ts}:R>)"` と相対時間表記が含まれていますが、不要であれば `deadline_str = f"<t:{deadline_ts}:f>"` に修正します。

## 提案する変更ファイル一覧
- `backend/src/services/schedule_poll_service.py`
  - 対象メソッド: `create_poll`, `send_reminder`
- `backend/src/services/attendance_tasks.py` (任意対応)
  - 対象メソッド: `_send_reminder`


## 確認事項・User Review Required
この方針について問題ないか、上記に提案した「送信するメッセージの文言・イメージ」で実装を進めてよろしいでしょうか？
よろしければ、実装フェーズに進みます。

## 検証計画 (Verification Plan)
- バックエンドのユニットテスト (`test_schedule_poll_service.py`) にて、`create_poll` および `send_reminder` 実行時に mock_discord_service に渡される引数 (`content` 文字列) の中に正しく `<t:...>` の文字列が含まれているかを確認します。
