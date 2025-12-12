# Azure Functions Deployment & Fixes Walkthrough

## 概要
本セッションでは、Azure Functions へのデプロイにおける複数の問題を解決し、ドキュメントを整備し、ユーザビリティ向上のために Discord Bot 招待リンクを実装しました。

## 実施した変更

### 1. バグ修正 (Azure Functions)
- **Script Upload 500 Error**:
    - `rehearsal_scenes` テーブルの外部キー制約違反を解決するため、削除順序を修正しました。
    - Azure Functions の Read-only File System エラーを回避するため、デバッグログのファイル出力を削除しました。
- **Scene Chart API 500 Error**:
    - `get_scene_chart` エンドポイントでの重複した `@router` デコレータを削除しました。
    - 未定義だった `current_user` 変数を `Depends` から取得した `member` を使用するように修正しました。

### 2. 環境設定 & デプロイ
- **API URL**:
    - フロントエンドの `API_URL` を `VITE_API_URL` 環境変数から取得するように修正し、本番環境で正しい Function App URL を使用するようにしました。
- **Static Web Apps**:
    - `staticwebapp.config.json` を追加し、SPAのルーティング設定を行いました。

### 3. ドキュメント更新
- **README.md**: Azure Functions と Static Web Apps のデプロイ情報を反映しました。
- **azure_functions_setup.md**: Static Web Apps の手順と、詳細なトラブルシューティングガイドを追加しました。
- **role_manual.md (全言語)**: 管理者向けに Discord Bot の招待手順とリンクを追加しました。

### 4. 機能追加
- **Discord Bot 招待リンク**:
    - プロジェクト設定画面（`ProjectSettingsPage.tsx`）に、Bot招待ボタンを追加しました（オーナーのみ表示）。
    - Client ID を含む招待リンクを設定しました。
    - 全5言語（ja, en, ko, zh-Hans, zh-Hant）に対応しました。

## 検証結果

### ✅ スクリプトアップロード
Azure Functions 環境でも 500 エラーが発生せず、正常にアップロードとデータクリーンアップ（再アップロード時）が行われることを確認しました。

### ✅ 香盤表表示
APIルートの修正により、香盤表の生成と取得が正常に行われるようになりました。

### ✅ Discord Bot 招待
プロジェクト設定画面から直接 Bot を招待できるようになり、UXが向上しました。

### ✅ マニュアル
管理者が必要な情報（Bot招待URLなど）にアクセスしやすくなりました。

### ✅ 出欠確認 (Interactions)
Discord Developer Portal の `Interactions Endpoint URL` を設定し、Azure Functions 側の `DISCORD_PUBLIC_KEY` 環境変数を設定することで、出欠確認ボタンが機能することを確認するための手順書を整備しました。
