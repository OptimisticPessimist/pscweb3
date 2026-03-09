# 修正確認 (Walkthrough): 招待URLからのDiscordログインフロー

## 問題の詳細
以前のバージョンでは、未ログイン状態でプロジェクトリンク（ `/invitations/:token` ）を踏み、「Discordでログイン」ボタンを押すと、プロセス完了後に**強制的に `/dashboard` にリダイレクト**されていました。これではユーザーがプロジェクト招待を承諾するページにたどり着けず、参加ボタンを押せないという課題がありました。

## 修正内容

### `frontend/src/pages/auth/LoginPage.tsx`
- 未ログインのユーザーが招待ページ等からリダイレクトされる際、内部で持っている現在のURL (`location.state.from`) を `localStorage` の `postLoginRedirect` というキー名で保存するようにしました。

### `frontend/src/pages/auth/AuthCallbackPage.tsx`
- Discordからのコールバック後、ログイン処理が完了したタイミングで、 `localStorage` に保持している `postLoginRedirect` の値をチェックするように変更しました。
- キーが存在していれば、ダッシュボードではなくその保存されたURLへリダイレクトさせます（直後にキーを削除）。

## 今後のフロー
これにより、対象の招待URLを開いた後、Discordでログイン操作を済ませた際、**再び元の招待ページへ戻っ**てくるようになります。ログイン状態になっているため、そのページには「参加する（Accept）」ボタンが表示され、問題なくプロジェクトに参加可能になります。
