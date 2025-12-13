# 脚本タイトル・著者抽出 実装計画

## 目標
脚本アップロードプロセスを強化し、アップロードされたFountainファイルから自動的に `Title`（タイトル）と `Author`（著者）のメタデータを抽出します。これらのフィールドはアップロードUIで自動入力（プレフィル）され、ユーザーの手入力を省くとともに、データベースに保存してUI表示やDiscord通知で利用できるようにします。

## 変更内容

### データベース
#### [MODIFY] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- `Script` テーブルに `author` カラムを追加します。
  - 型: `String(100)` 程度。
  - Nullable: True（すべての脚本に著者があるとは限らないため）。

#### [NEW] [alembic revision]
- `scripts` テーブルに `author` カラムを追加するマイグレーションスクリプトを作成します。

### バックエンド
#### [MODIFY] [schemas/script.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/script.py)
- `ScriptResponse` スキーマを更新し、`author` フィールドを含めます。

#### [MODIFY] [services/fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- `parse_fountain_and_create_models`（またはラッパー関数）を更新し、`fountain` ライブラリの `metadata` 属性を使用してメタデータ（`Title`, `Author`, `Credit` など）を抽出できるようにします。
- 抽出された `author` 情報を `Script` オブジェクトに反映させます（必要な場合）。
- 今回の方針:
  - アップロード時にフロントエンドから送信された `Title` と `Author` を優先して保存します（ユーザーが編集可能なため）。
  - バックエンド側でもパース時に抽出可能ですが、基本はAPIで受け取ったデータを正とします。

#### [MODIFY] [api/scripts.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/scripts.py)
- `upload_script` エンドポイントを更新し、オプションの `author` フォームフィールドを受け付けるようにします。
- `process_script_upload` 関数に `author` を渡します。

#### [MODIFY] [services/script_processor.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/script_processor.py)
- `get_or_create_script` 関数を更新し、`author` を受け取って `Script` モデルに保存するようにします。

#### [MODIFY] [services/script_notification.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/script_notification.py)
- 通知メッセージを更新し、著者情報が存在する場合は "Author: [author]" を含めるようにします。

### フロントエンド
#### [MODIFY] [ScriptUploadPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/ScriptUploadPage.tsx)
- `onDrop` コールバックを更新し、`FileReader` を使用してファイルの内容を読み込みます。
- 最初の数行（ヘッダー部分）を解析し、"Title:", "Author:", "Credit:" などのキーを見つけます。
- `Title` の形式: Fountain仕様に従い `key: value` を解析します。
- `title` ステートを自動入力（プレフィル）します。
- `author` ステートと入力フィールド（任意項目）を追加し、同様に自動入力します。
- `handleSubmit` を更新し、`FormData` に `author` を追加して送信します。

## 検証計画

### 自動テスト
1. **Backend Unit Test**: `tests/unit/test_api_scripts.py` -> `test_upload_script` を更新します。
   - アサーション追加: `assert data["author"] == "Test Author"`。
   - 実行コマンド: `pytest tests/unit/test_api_scripts.py`

### 手動検証
1. **アップロードフロー**:
   - プロジェクト -> 脚本 -> アップロード画面へ移動。
   - TitleとAuthorが含まれる有効なFountainファイルをドロップ。
   - 以下の挙動を確認:
     - タイトル入力欄が自動入力されること。
     - 著者入力欄が自動入力されること。
   - アップロードボタンをクリック。
   - 脚本一覧画面への遷移を確認。
   - 一覧または詳細画面で著者が表示されているか確認（UIに追加した場合）。

2. **Discord通知**:
   - 設定されたDiscordチャンネルを確認。
   - 通知メッセージに著者名が含まれていることを確認。
