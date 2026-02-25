# 実装計画: Discordスケジュール通知へのICSファイル追加 (機能: 38-add-ics-file-discord)

## 目的
現在、新規で稽古（リハーサル）を追加した際にはICS（iCalendar形式のファイル）がDiscordへ送信されているが、その後の**スケジュール更新時**(`update_rehearsal`)や**日程調整からのスケジュール確定時**(`finalize_poll`)にはICSファイルが添付されていない。
これらにICSファイルの生成・添付処理を追加することで、ユーザーがスマートフォンのカレンダーアプリなどにスケジュールの更新や確定をワンタップで登録できるようにする。

## 実装内容詳細

### 1. `backend/src/api/rehearsals.py` (`update_rehearsal`) の修正
- 既存の `add_rehearsal` にある ICS ファイル生成ロジック（`BEGIN:VCALENDAR` ... `END:VCALENDAR`を文字列フォーマットで生成する部分）を再利用・移植する。
- スケジュールに変更（時間や場所など）があった場合、その新しい時間などを開始時刻(`DTSTART`)・終了時刻(`DTEND`)に設定する。
- 通知メッセージ内に `file=ics_file` を追加する。
- 必要なライブラリ(`uuid`, `datetime`, `timedelta`)のインポートがあるか確認（既存のファイル内にはあるはず）。

### 2. `backend/src/api/schedule_polls.py` (`finalize_poll`) の修正
- ここにも同様の ICS 生成ロジックを追加。
- タイトル(`SUMMARY`)を日程調整確定用などに合わせ、稽古場所や時間を含める。
- `background_tasks.add_task` メソッドの引数に `file=ics_file` を追加。
- `uuid`, `datetime` のモジュールを使うため、不足していればファイルの先頭でインポートしておく。

## 検証計画
- `uv run pytest tests/` でテストを実行し、テストが通ることを確認。
- 最終的に `walkthrough.md` に実施した事項をまとめて完了とする。
