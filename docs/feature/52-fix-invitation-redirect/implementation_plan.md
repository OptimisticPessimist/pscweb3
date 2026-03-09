# Implementation Plan: 招待後のリダイレクト修正

## 1. LoginPage.tsxの改修
- ログイン画面への遷移時に渡された `state.from` を `localStorage` (キー名: `postLoginRedirect`) に保存する
- 既存の処理は残しつつ、DiscordのOAuth認証へ処理を引き継ぐ

## 2. AuthCallbackPage.tsxの改修
- Discordからのコールバック時に取得したトークンを使ってログイン状態にする
- ログイン完了後、 `localStorage` に `postLoginRedirect` があるか調べ、存在した場合はそのURLに `navigate()` する。その後キーを削除する。
- 存在しない場合は、従来通り `/dashboard` へ遷移する。
