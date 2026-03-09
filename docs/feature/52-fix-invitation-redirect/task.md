# Task: 招待後のリダイレクト修正

## 課題
プロジェクトへの招待URLからDiscord認証を行った後、元の招待ページに戻らずにダッシュボードにリダイレクトされてしまい、参加ボタンを押すことができない状態になっていた。

## 解決策
1. `LoginPage.tsx` で遷移元のURL (`location.state.from`) を `localStorage` に保存する
2. `AuthCallbackPage.tsx` で認証に成功した後、 `localStorage` を確認し、遷移元のURLがあればそこにリダイレクトする（なければダッシュボードへ遷移）
