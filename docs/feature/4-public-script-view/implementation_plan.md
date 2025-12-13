# 公開脚本閲覧・インポート機能 実装計画

## 概要
脚本の公開閲覧機能（PDFダウンロード不可）と、公開された脚本を自身のプロジェクトに取り込む（インポート）機能を実装します。

## 変更内容

### Backend

#### API (`src/api/public.py` or `src/api/scripts.py`)
- [NEW] `GET /api/public/scripts/{script_id}`
    - 認証不要。
    - `is_public=True` の場合のみスクリプト情報を返す。
    - PDFダウンロードリンクは含めない（またはPDF生成エンドポイントは認証必須のままにする）。

#### API (`src/api/projects.py`)
- [NEW] `POST /api/projects/import-script`
    - 認証必須。
    - 公開されている `script_id` を受け取り、新規プロジェクトを作成してその脚本をコピーする。
    - **プロジェクト作成上限（2つ）のチェックを行う**。

### Frontend

#### Routes (`src/routes/index.tsx`, `src/App.tsx`)
- [NEW] `/public/scripts/:scriptId`
    - 公開レイアウト（サイドバーなし、ヘッダーのみ？）または専用レイアウトを使用。

#### Pages
- [NEW] `src/features/scripts/pages/PublicScriptPage.tsx`
    - `ScriptDetailPage` をベースにするが、編集・削除・PDFダウンロード機能を削除。
    - **「この脚本を使ってプロジェクトを作成」ボタン**を配置。

#### Components
- `ScriptDetailPage` から表示コンポーネントを切り出して再利用するか、または `ScriptDetailPage` 内部で `isPublicView` フラグで制御するか検討。
    - `PublicScriptPage` は独立させた方が安全（誤って編集ボタンが出ないように）。
    - 共通部分は `ScriptViewer` コンポーネントとして切り出すのが理想。

## 検証計画

### 自動テスト
- `GET /api/public/scripts/{script_id}`
    - `is_public=False` の脚本にアクセスできないこと。
    - `is_public=True` の脚本に未認証でアクセスできること。
- `POST /api/projects/import-script`
    - プロジェクト上限に達しているユーザーが実行してエラーになること。
    - 正常にプロジェクトが作成され、脚本がコピーされること。

### 手動検証
1. ログインし、脚本を「公開」設定にする。
2. ログアウト（またはシークレットウィンドウ）して、公開URLにアクセス。
    - 脚本内容が見れること。
    - PDFダウンロードボタンがないこと。
3. ログインして、公開ページから「プロジェクトを作成」を実行。
    - 新しいプロジェクトが作られ、脚本が入っていること。
