# 実装計画: Discord通知の重複送信修正

## 1. 現状分析と原因調査
### 現状の動作
- 脚本がアップロード/更新されると、`backend/src/api/scripts.py` から `send_script_notification` がバックグラウンドタスクとして呼び出される。
- `send_script_notification` はPDFを生成し、`DiscordService.send_notification` を使用してDiscordのWebhookにPOSTする。
- `DiscordService._request_with_retry` は `httpx.AsyncClient` をデフォルト設定で使用しており、そのタイムアウトは5秒である。

### 推測される原因
1. **タイムアウトによる重複**: 
   PDF添付を含むDiscordへのPOSTリクエストが5秒を超過すると、`httpx.HTTPError` (TimeoutException) が発生する。
2. **不適切なリトライ**: 
   `_request_with_retry` は `HTTPError` が発生すると最大3回までリトライする。
   Discord側ではリクエストを受理して処理中であっても、クライアント側がタイムアウトで切断してリトライすると、Discordは複数回のリクエストを受け取ることになり、結果として複数の通知が飛ぶ。

## 2. 修正方針
1. **タイムアウト設定の延長**:
   `httpx.AsyncClient` のタイムアウトを30秒に延長する。これにより、PDFのアップロードが5秒を超えても正常に完了を待機できるようになる。
2. **リトライ条件の適正化**:
   - レート制限(429)や、サーバー側の一時的なエラー(502, 503, 504)などはリトライすべきだが、POSTリクエストにおける一般的なネットワークエラーやタイムアウトでのリトライは、今回のような重複を引き起こすため注意が必要。
   - ただし、まずはタイムアウトの延長で解決するかを確認する。

## 3. 具体的な変更内容
### backend/src/services/discord.py
- `_request_with_retry` メソッド内で `httpx.AsyncClient` を生成する際に、`timeout=30.0` を指定する。

## 4. 期待される効果
- ネットワークやDiscordの応答が少々遅れても、タイムアウトせずに1回の送信で完了する。
- 重複通知が解消される。
