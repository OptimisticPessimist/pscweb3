# タスクリスト
- [x] 招待ページ(InvitationLandingPage.tsx)のDiscordログイン遷移時、`localStorage`の`postLoginRedirect`に`auto_accept=true`を付与する
- [x] 招待ページ(InvitationLandingPage.tsx)の初期ロード時、`auto_accept=true`が存在し、かつユーザーがログインしていれば、自動で招待承認APIを叩く
- [x] （必要に応じて）自動参加処理中にローディング表示等を追加する
- [x] 動作確認（非ログイン状態で招待URLアクセス -> Discordログイン -> 自動参加 -> プロジェクト詳細画面への遷移）
