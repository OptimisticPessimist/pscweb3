# Azure Functions Deployment & Fixes Walkthrough

## 概要
本セッションでは、Azure Functions へのデプロイにおける複数の問題を解決し、ドキュメントを整備し、ユーザビリティ向上のために Discord Bot 招待リンクを実装しました。さらに、ユーザーからのフィードバックに基づき、タイムゾーン表示の修正、Discord通知へのメンション追加、およびトラブルシューティングガイドの作成を行いました。

## 実施した変更

### 1. バグ修正 (Azure Functions & Timezone)
- **Script Upload 500 Error**: `rehearsal_scenes` テーブルの外部キー制約違反修正、ログ出力設定変更。
- **Scene Chart API 500 Error**: 重複ルート修正、未定義変数修正。
- **My Schedule Timezone**: `get_my_schedule` APIが返す日時に UTC タイムゾーン情報を付与し、フロントエンドでの JST 表示ズレ（前日15時になる問題）を解消しました。

### 2. 環境設定 & デプロイ
- **API URL**: `VITE_API_URL` 環境変数対応。
- **Static Web Apps**: `staticwebapp.config.json` 設定。

### 3. ドキュメント更新
- **README.md / azure_functions_setup.md / role_manual.md**: デプロイ手順、Bot招待手順を更新。
- **[NEW] attendance_debug_manual.md**: 出欠確認（Interactions Endpoint）の設定方法、環境変数、動作確認手順をステップバイステップで解説したガイドを作成しました。

### 4. 機能追加
- **Discord Bot 招待リンク**: プロジェクト設定画面への追加。
- **メンション機能**: 稽古追加時のDiscord通知に、対象となる参加者・キャストへのメンション (`<@user_id>`) を追加しました。

## 検証結果

### ✅ スクリプトアップロード & 香盤表
Azure Functions 環境での正常動作を確認（前提）。

### ✅ マニュアル & ガイド
管理者向け手順と、トラブルシューティングガイドを整備しました。

### ✅ 出欠確認 (Interactions)
Discord Developer Portal の設定に必要な情報（Public Key, Endpoint URL）を明確化し、トラブル時の確認フローを確立しました。
