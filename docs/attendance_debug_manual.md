# 出欠確認機能 トラブルシューティングガイド

出欠確認機能が動かない（通知が来ない、ボタンが反応しない）場合の確認手順をまとめました。

## 1. 前提条件の確認

まず、最低限必要な設定ができているか確認してください。

### 1-1. Discord Bot の招待
プロジェクト設定画面（オーナーのみ表示）にある「🤖 Botを招待」ボタンから、DiscordサーバーにBotを招待済みですか？
- Botがサーバーに参加していないと、メッセージ送信もメンションもできません。

### 1-2. チャンネル設定
プロジェクト設定画面で「出欠確認通知チャンネル」のIDが正しく入力されていますか？
- **確認方法**: Discordでチャンネルを右クリック -> 「チャンネルIDをコピー」（開発者モードがONである必要があります）

## 2. Azure Function App の環境変数

Azure Portal で Function App (`pscweb3-functions-...`) を開き、「設定」→「環境変数」を確認してください。以下の変数が必須です。

| 変数名 | 値の例/説明 |
| :--- | :--- |
| `DISCORD_PUBLIC_KEY` | Discord Dev Portal の "General Information" にある **Public Key** をコピーして貼り付けます。<br>※これがないとボタン機能が動きません（500エラーになります）。 |
| `DISCORD_BOT_TOKEN` | Discord Bot Token |
| `DATABASE_URL` | Neon/Postgres接続文字列 |

**変更後は必ず「適用」をクリックし、数分待ってください。**

## 3. Discord Developer Portal の設定

Webブラウザで [Discord Developer Portal](https://discord.com/developers/applications) を開きます。

### 3-1. Interactions Endpoint URL
左メニュー「General Information」の下の方にあります。
ここに以下のURLが設定されている必要があります：
```
https://<あなたのFunctionApp名>.azurewebsites.net/api/discord/interactions
```
**設定時のエラーについて**:
- 「Authentication failed（認証できませんでした）」と出る場合、以下の可能性が高いです：
    1. Azure側の `DISCORD_PUBLIC_KEY` が間違っている、または設定後に再起動が完了していない。
    2. URLが間違っている（`/api/discord/interactions` まで含めていない）。
    3. Azure Function App が停止している。

## 4. 動作確認の手順

設定が完了したら、以下の手順で動作を確認します。

### Step 1: 稽古を作成する
1. Webアプリの「マイスケジュール」または「プロジェクト詳細」から、新しい稽古を追加します。
2. **「出欠確認を作成する」** にチェックを入れます（重要）。
3. 期限などを設定して「保存」します。

### Step 2: Discord通知の確認
作成後すぐに、設定したDiscordチャンネルに以下のようなメッセージが届くか確認します。

> **稽古出席確認: シーン名**
> ...
> [参加] [不参加] [保留]

- **届かない場合**: `DISCORD_BOT_TOKEN` または `チャンネルID` が間違っている可能性があります。Webアプリの使用においてエラー画面が出たかどうかも確認ポイントです。

### Step 3: ボタンの反応確認
届いたメッセージの「参加」ボタンを押します。
- **「✅ ステータスを「参加」に更新しました」** と（自分だけに）表示されれば成功です。
- **「Interaction Failed」と出る場合**: Interactions Endpoint URL が正しく設定されていません。

### Step 4: リマインダー（自動実行）の確認
これを確認するのは少し難しいですが、以下の方法があります。

1. **Azure Portal** で Function App を開く。
2. 左メニュー「関数」→ `schedule_attendance_reminder` をクリック。
3. 「監視」→「ログストリーム」を開いておく。
4. 30分ごとの定時実行のタイミング（毎時0分と30分）に、ログが流れるか確認します。
   - `Found X expired events to check` のようなログが出れば正常に動いています。

## よくある質問

**Q. 0時に設定したはずの稽古が、カレンダーで前日の15時に表示されます。**
A. タイムゾーンの設定によるズレです。現在は修正を行いましたので、新しく作成する稽古、または表示をリロードすることで解消されるはずです。（内部的にはUTCで保存されており、正しく+9時間されてJST 0時として表示されるようになります）

**Q. メンションが飛びません。**
A. ユーザー設定で Discord ID が紐付いていないとメンションできません。
   - アプリ右上のユーザーアイコン → 「設定」から Discord連携を行ってください。
   - または、管理者がメンバーリストから手動で Discord ID を入力することも可能です。
