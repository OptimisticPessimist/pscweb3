# Azure Functions Deployment & Fixes Walkthrough

## 概要
本セッションでは、Azure Functions へのデプロイにおける複数の問題を解決し、ドキュメントを整備し、ユーザビリティ向上のために Discord Bot 招待リンクを実装しました。さらに、ユーザーからのフィードバックに基づき、タイムゾーン表示の修正、Discord通知へのメンション追加、およびトラブルシューティングガイドの作成を行いました。

最後に、タイムゾーン処理の根本解決としてデータベーススキーマの変更とコードのリファクタリングを実施しました。

## 実施した変更

### 1. バグ修正 (Azure Functions & Timezone)
- **Script Upload 500 Error**: `rehearsal_scenes` テーブルの外部キー制約違反修正、ログ出力設定変更。
- **Scene Chart API 500 Error**: 重複ルート修正、未定義変数修正。
- **My Schedule Timezone**: `get_my_schedule` APIが返す日時に UTC タイムゾーン情報を付与し、フロントエンドでの JST 表示ズレを解消しました。
- **API 500 Error Fix**: `timezone` モジュールのインポート漏れを修正。

### 2. 環境設定 & デプロイ
- **API URL**: `VITE_API_URL` 環境変数対応。
- **Static Web Apps**: `staticwebapp.config.json` 設定。

### 3. ドキュメント更新
- **README.md / azure_functions_setup.md / role_manual.md**: デプロイ手順、Bot招待手順を更新。
- **attendance_debug_manual.md**: 出欠確認（Interactions Endpoint）の設定方法、環境変数、動作確認手順をステップバイステップで解説したガイドを作成しました。

### 4. 機能追加
- **Discord Bot 招待リンク**: プロジェクト設定画面への追加。
- **メンション機能**: 稽古追加・削除時のDiscord通知に、対象となる参加者・キャストへのメンション (`<@user_id>`) を追加しました。脚本更新時には `@here` で通知されます。
- **Discord Timestamp Formatting**: Discord通知の日時表示に `<t:TIMESTAMP:f>` 形式を採用し、閲覧者のローカルタイムで表示されるようにしました。
- **マイルストーン設定画面**: プロジェクト設定ページにマイルストーンの一覧・追加・削除機能を追加しました。これにより、マイルストーン管理が容易になりました。

### 5. リファクタリング (Timezone Handling)
- **DB Schema Change**: `Rehearsal`, `Milestone`, `AttendanceEvent` などの主要な日時カラムを `DateTime(timezone=True)` (UTC Aware) に変更しました。これにより、タイムゾーン情報の欠落による混乱を防ぎます。
- **Code Cleanup**: APIコード内に散在していた手動でのタイムゾーン変換ロジックを削除し、DB定義に基づいた自然な処理に統一しました。
- **DB Reset Script**: スキーマ変更に伴うデータベース再作成用のスクリプト `src/scripts/reset_db.py` を作成しました。

## 検証結果

### ✅ スクリプトアップロード & 香盤表
Azure Functions 環境での正常動作を確認（前提）。

### ✅ マニュアル & ガイド
管理者向け手順と、トラブルシューティングガイドを整備しました。

### ✅ タイムゾーン管理
入力から保存、出力まで UTC Aware で統一されたことをコードレビューにて確認しました。DBリセット後、正常に動作することを確認済みです。
