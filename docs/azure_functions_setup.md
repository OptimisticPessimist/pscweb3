# Azure Functions セットアップ手順

この手順書では、Azure Functions Appを作成し、GitHub Actionsで自動デプロイを設定する手順を説明します。

## 1. Azure Function App の作成

### 1-1. Azure Portal でリソース作成

1. [Azure Portal](https://portal.azure.com/) にアクセスし、ログインします。

2. **「リソースの作成」** → **「関数アプリ」** を検索してクリックします。

3. 以下の設定を行います：

   | 項目 | 設定値 |
   |------|--------|
   | **サブスクリプション** | お使いのサブスクリプション |
   | **リソースグループ** | `rg-pscweb3` (既存) または新規作成 |
   | **関数アプリ名** | `pscweb3-functions` (グローバルでユニーク) |
   | **ランタイムスタック** | Python |
   | **バージョン** | 3.12 |
   | **オペレーティングシステム** | **Windows** ← 推奨 |
   | **地域** | Japan East |
   | **ホスティングオプション** | **従量課金** |

   > [!IMPORTANT]
   > **Windows 従量課金プランを推奨する理由**
   > - 無料枠: **100万回/月** (Linux Flex は25万回)
   > - 無料枠: **400,000 GB秒/月** (Linux Flex は10万GB秒)
   > - 複数の劇団・クリエイターが利用しても無料枠内で収まりやすい

4. **「次: ストレージ」** をクリックし、ストレージアカウントを選択または新規作成します。

5. **「確認および作成」** → **「作成」** をクリックしてデプロイを開始します（2-3分かかります）。

### 1-2. 環境変数の設定

Function Appが作成されたら、以下の環境変数を設定します：

1. Function App のリソースページに移動します。
2. **「設定」 → 「環境変数」** をクリックします。
3. **「+ 追加」** をクリックして以下を追加します：

   | 名前 | 値 |
   |------|-----|
   | `DATABASE_URL` | Neon/SupabaseのPostgreSQL接続文字列 |
   | `JWT_SECRET_KEY` | バックエンドと同じシークレットキー |
   | `DISCORD_BOT_TOKEN` | Discordボットトークン（通知送信用） |

4. **「保存」** をクリックします。

## 2. GitHub シークレットの設定

### 2-1. 発行プロファイルの取得

1. Azure Portal で作成した Function App のリソースページに移動します。
2. **「概要」** ページの上部にある **「発行プロファイルの取得」** をクリックします。
3. `.PublishSettings` ファイルがダウンロードされます。
4. ファイルをテキストエディタで開き、**内容全体をコピー**します。

> [!NOTE]
> 発行プロファイルがダウンロードできない場合は、「設定」→「構成」→「全般設定」で「基本認証」を有効にしてください。

### 2-2. GitHub にシークレット登録

1. GitHubリポジトリ (https://github.com/OptimisticPessimist/pscweb3) を開きます。
2. **「Settings」 → 「Secrets and variables」 → 「Actions」** に移動します。
3. **「New repository secret」** をクリックし、以下を追加します：

   | 名前 | 値 |
   |------|-----|
   | `AZURE_FUNCTIONAPP_NAME` | `pscweb3-functions` (作成したFunction App名) |
   | `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` | 発行プロファイルの内容（XMLテキスト全体） |

4. **「Add secret」** をクリックして保存します。

> [!IMPORTANT]
> **既存シークレットの変更**
> - `AZURE_WEBAPP_PUBLISH_PROFILE` は不要になります（削除可）
> - `VITE_API_URL` は Azure Functions の URL に更新してください
>   - 例: `https://pscweb3-functions.azurewebsites.net`

## 3. デプロイの実行

### 3-1. 手動デプロイ（初回テスト）

1. GitHubリポジトリの **「Actions」** タブに移動します。
2. 左サイドバーから **「Azure Functions Deployment」** を選択します。
3. **「Run workflow」** → **「Run workflow」** をクリックします。
4. ワークフローが成功することを確認します。

### 3-2. 自動デプロイ

以降は、`main` ブランチに `backend/` 配下の変更がプッシュされると自動的にデプロイされます。

## 4. 動作確認

### 4-1. Azure Portal で Timer 実行を確認

1. Function App のリソースページに移動します。
2. 左サイドバーの **「関数」** をクリックします。
3. `schedule_attendance_reminder` 関数が表示されていることを確認します。
4. **「監視」** → **「ログストリーム」** を開き、30分ごとにログが出力されることを確認します。

### 4-2. テスト実行（オプション）

Timer Functionを手動でテスト実行するには：

1. Function App の **「関数」** → `schedule_attendance_reminder` をクリック
2. **「コードとテスト」** を選択
3. **「テストと実行」** をクリック
4. リクエスト本文に `{}` を入力して **「実行」**

## トラブルシューティング

### デプロイ失敗の場合

1. GitHub Actionsのログを確認
2. Azure Portal の「デプロイセンター」→「ログ」を確認
3. 必要な環境変数がすべて設定されているか確認

### Timer が実行されない場合

1. Function App が実行中か確認（停止していないか）
2. 「関数」一覧に関数が表示されているか確認
3. Application Insights でエラーログを確認
