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

   | 名前 | 値 | 説明 |
   |------|-----|------|
   | `DATABASE_URL` | `postgresql+asyncpg://...` | Neon/SupabaseのPostgreSQL接続文字列 |
   | `JWT_SECRET_KEY` | (任意の文字列) | JWT認証用シークレットキー |
   | `DISCORD_CLIENT_ID` | Discord Dev Portal から | Discord OAuthクライアントID |
   | `DISCORD_CLIENT_SECRET` | Discord Dev Portal から | Discord OAuthクライアントシークレット |
   | `DISCORD_BOT_TOKEN` | Discord Dev Portal から | Discordボットトークン（通知送信用） |
   | `DISCORD_PUBLIC_KEY` | Discord Dev Portal から | Discord公開鍵（Interactions検証用） |
   | `DISCORD_REDIRECT_URI` | `https://<function-app>.azurewebsites.net/auth/callback` | Discord OAuth リダイレクトURI |
   | `FRONTEND_URL` | `https://<static-web-app>.azurestaticapps.net` | Static Web AppsのURL |
   | `SENDGRID_API_KEY` | `SG.xxx...` | SendGrid APIキー |
   | `FROM_EMAIL` | `noreply@yourdomain.com` | メール送信元アドレス |
   | `FROM_NAME` | `PSC Web` | メール送信者名 |
   | `REPLY_TO_EMAIL` | `support@yourdomain.com` | 返信先アドレス |

4. **「保存」** をクリックします。

> [!IMPORTANT]
> `DISCORD_REDIRECT_URI` は Function App のURLを使用します。Discord Developer Portal の OAuth2 Redirects にも同じURLを登録してください。

### 1-3. Discord Developer Portal の設定

出欠確認機能（Interactions）を使用するには、Discord Developer Portal で以下の設定が必要です：

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセスし、アプリケーションを選択します。
2. 左メニューの **「General Information」** にある **「PUBLIC KEY」** をコピーし、上記環境変数 `DISCORD_PUBLIC_KEY` に設定します。
3. **「Interactions Endpoint URL」** に Function App のURLを設定します：
   ```
   https://<function-app-name>.azurewebsites.net/api/discord/interactions
   ```
4. **「Save Changes」** をクリックします。

> [!NOTE]
> 設定時にDiscordがエンドポイントに検証リクエストを送信します。Function Appがデプロイされ、環境変数が設定された後でないと保存できません。

### 1-4. SendGrid の設定

メール通知機能を使用するには SendGrid の設定が必要です：

1. [SendGrid](https://sendgrid.com/) でアカウントを作成（無料プランあり）。
2. **Settings → API Keys** で API Key を作成し、上記環境変数 `SENDGRID_API_KEY` に設定します。
3. **Settings → Sender Authentication** で送信元メールアドレス（`FROM_EMAIL`）の認証を行います。
   - 独自ドメイン推奨ですが、Single Sender Verification でGmailアドレス等も使用可能です。

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

### API コールが失敗する場合

1. **CORS設定**: Function App「API」→「CORS」で フロントエンドURLを許可しているか確認
2. **環境変数**: `FRONTEND_URL` が正しく設定されているか確認
3. **Discord OAuth**: `DISCORD_REDIRECT_URI` が Function App の URL になっているか確認

### 500エラーが発生する場合

1. Azure Portal の **「監視」→「ログストリーム」** でエラー詳細を確認
4. 主な原因:
   - **Discord Interactions エラー**: `DISCORD_PUBLIC_KEY` が環境変数に設定されていない場合、署名検証に失敗し 500 エラーになります。
   - **データベース接続エラー**: `DATABASE_URL` の確認
   - **外部キー制約エラー**: 関連データの削除順序
   - **読み取り専用ファイルシステム**: Azure Functionsでのファイル書き込み（ログ出力など）はエラーになります。

---

## 5. Azure Static Web Apps のセットアップ

### 5-1. Azure Portal でリソース作成

1. **「リソースの作成」** → **「Static Web App」** を検索してクリック
2. 以下の設定を行います：

   | 項目 | 設定値 |
   |------|--------|
   | **サブスクリプション** | お使いのサブスクリプション |
   | **リソースグループ** | `rg-pscweb3` (既存) |
   | **名前** | `pscweb3-frontend` |
   | **ホスティングプラン** | **Free** |
   | **地域** | East Asia |
   | **ソース** | GitHub |
   | **組織** | あなたのGitHubアカウント |
   | **リポジトリ** | `pscweb3` |
   | **ブランチ** | `main` |

3. **ビルドの詳細**:
   - **ビルドプリセット**: `React`
   - **アプリの場所**: `/frontend`
   - **API の場所**: (空欄)
   - **出力先**: `dist`

4. **「確認および作成」** → **「作成」**

### 5-2. 環境変数の設定

Static Web Apps にビルド時環境変数を設定します：

1. GitHub リポジトリの **「Settings」→「Secrets and variables」→「Actions」**
2. 以下のシークレットを追加：

   | 名前 | 値 |
   |------|-----|
   | `VITE_API_URL` | Function App の URL (例: `https://pscweb3-functions-*.azurewebsites.net`) |

### 5-3. SPAルーティング設定

`frontend/staticwebapp.config.json` ファイルでSPAルーティングを設定しています：

```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/assets/*", "/api/*"]
  }
}
```

> [!NOTE]
> このファイルはビルド後に `dist` フォルダにコピーされます（GitHub Actions ワークフローで設定済み）。

## 6. データベースマイグレーション（本番環境）

Azure Functions上のアプリケーションが参照するデータベース（Neon等）に対して、テーブル作成や変更を適用する手順です。

推奨される方法は、**ローカル環境からリモートデータベースに対して Alembic を実行する**ことです。

### 手順

1. `backend/.env` ファイルの `DATABASE_URL` を、**本番環境のデータベース接続文字列** に書き換えます。
   ```ini
   DATABASE_URL=postgresql+asyncpg://user:password@endpoint.neon.tech/neondb
   ```
   > ⚠️ **注意**: 作業が終わったら、必ずローカル開発用のURLに戻してください。

2. マイグレーションを実行します。
   ```bash
   cd backend
   uv run alembic upgrade head
   ```

3. 完了したら `.env` を元に戻します。
