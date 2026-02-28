# Azure Blob Storage の設定と管理ガイド

プレミアム機能（プロジェクト作成上限の拡張）の設定を Azure Blob Storage で管理するための手順です。

## 1. Azure Blob Storage の準備

### ストレージアカウントの作成
より詳細な手順は以下の通りです：

1. **Azure Portal にログイン**: [portal.azure.com](https://portal.azure.com) にアクセスします。
2. **リソースの作成**: 「リソースの作成」をクリックし、「ストレージ アカウント」を検索して選択し、「作成」をクリックします。
3. **基本設定**:
   - **プロジェクトの詳細**: 適切なサブスクリプションとリソースグループを選択します。
   - **ストレージアカウント名**: 世界で一意な名前を入力します（例: `pscpromonthlyconfig`）。
   - **地域**: 本システムが稼働している地域と同じものを選択します（例: `Japan East`）。
   - **パフォーマンス**: 「Standard」を選択します。
   - **冗長性**: 最小コストの「ローカル冗長ストレージ (LRS)」を選択します。
4. **詳細設定 / ネットワーク**: デフォルト設定で問題ありませんが、セキュリティを高める場合は必要に応じて制限を行ってください。
5. **作成**: 「確認および作成」をクリックし、検証完了後に「作成」をクリックします。

### 接続文字列の取得
1. 作成したストレージアカウントの管理画面を開きます。
2. 左メニューの「セキュリティとネットワーク」>「アクセス キー」をクリックします。
3. `key1`（または `key2`）の「接続文字列 (Connection String)」にある「表示」をクリックし、内容をコピーします。
4. この値を環境変数 `AZURE_STORAGE_CONNECTION_STRING` に設定します。

### コンテナーの作成
1. ストレージアカウント管理画面の左メニュー「データ ストレージ」>「コンテナー」をクリックします。
2. 「＋ コンテナー」をクリックします。
   - 名前: `configs`（後述の環境変数で変更可能）
   - パブリック アクセス レベル: **プライベート (匿名アクセスなし)**
3. 「作成」をクリックします。

## 2. 設定ファイルの配置

コンテナー内に `premium_settings.json` という名前のファイルをアップロードします。

### ファイル形式 (`premium_settings.json`)
```json
{
  "tier1": {
    "password": "your_tier1_password_here",
    "limit": 2
  },
  "tier2": {
    "password": "your_tier2_password_here",
    "limit": 5
  },
  "test": {
    "password": "test_only_password",
    "limit": 999
  },
  "default_limit": 1,
  "last_rotation_month": "2026-03"
}
```

## 3. パスワードの自動更新機能

本システムには、月替わりでパスワードを自動更新する機能が組み込まれています。

### 仕組み
1. システム起動時、または定期的な設定リフレッシュ時に、現在の月と `last_rotation_month` を比較します。
2. 月が更新されている場合、新しいパスワード（英数字のランダム文字列）を自動生成し、Blob Storage のファイルを上書きします。
3. デフォルト設定では、Tier 1 と Tier 2 の両方のパスワードが更新されます。

### 手動での更新
Blob Storage 上の `premium_settings.json` を直接編集して保存することで、システムに即座に反映（最大5分間のキャッシュあり）させることができます。

## 4. 環境変数リファレンス

| 変数名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage への接続文字列 | (必須) |
| `PREMIUM_CONFIG_CONTAINER` | 設定ファイルを保存するコンテナー名 | `configs` |
| `PREMIUM_CONFIG_BLOB_NAME` | 設定ファイル名 | `premium_settings.json` |
| `PREMIUM_PROJECT_LIMIT_TIER1` | Blobが無い場合のデフォルト上限 (Tier1) | `2` |
| `PREMIUM_PROJECT_LIMIT_TIER2` | Blobが無い場合のデフォルト上限 (Tier2) | `5` |
