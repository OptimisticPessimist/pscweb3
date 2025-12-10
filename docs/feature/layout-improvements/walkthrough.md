# Walkthrough - UI Improvements & User Profile

## Overview
ユーザーからの要望（パンくずリスト導入、サイドバーのユーザー情報改善）に基づき、レイアウトとユーザープロファイル機能を強化しました。

## Changes

### 1. User Profile
- **Backend**: `User` モデルを拡張し、Discordの `avatar_url` (Avatar Hashから生成)、`display_name` (Global Name)、`email` を保存するようにしました。ログイン時にこれらの情報は自動的に更新されます。
- **Frontend**: サイドバーのユーザー表示を更新し、アイコン（アバター画像）、スクリーンネーム（表示名）、アカウントID（Discordユーザー名）を表示するようにしました。

### 2. Navigation
- **Breadcrumbs**: ヘッダー部分にパンくずリストを追加しました。
  - プロジェクト詳細画面などでは、URLのIDからプロジェクト名を非同期で解決して表示します。
  - これにより、現在の階層が明確になり、ユーザーのナビゲーション効率が向上しました。

## Verification
- **Sidebar**: ログイン後、自身のDiscordアバターと表示名がサイドバー下部に表示されることを確認。
- **Breadcrumbs**: プロジェクトページ遷移時に「Dashboard > Project Name > ...」のようにパンくずが表示されることを確認。
