# 公開脚本インポート時のプロジェクト制限バグ修正

## 実施内容

### 修正概要
公開脚本からプロジェクトをインポートする際 (`import_script`)、従来は「公開プロジェクト」として作成されていましたが、これを「非公開プロジェクト」として作成するように変更しました。
これにより、以下の効果があります：
1. **プロジェクト数制限の適用**: 非公開プロジェクトとしてカウントされるため、作成数上限（2つ）を超える場合はエラー（400 Bad Request）となります。
2. **ポリシーの統一**: `create_project` APIと同様に、他者の著作物を含むプロジェクトとして非公開を強制します。

### 変更ファイル
- [`backend/src/api/projects.py`](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)

```python
# Before
await check_project_limit(current_user.id, db, new_project_is_public=True)
...
new_project = TheaterProject(..., is_public=True)

# After
await check_project_limit(current_user.id, db, new_project_is_public=False)
...
new_project = TheaterProject(..., is_public=False)
```

## 検証結果

### 自動テスト
- **再現テスト (`test_bug_fix_limit.py`)**: 修正前は制限を回避して成功していたものが、修正後は期待通り `400 Bad Request` エラーとなり、制限が機能していることを確認しました。
- **回帰テスト (`test_api_projects.py`)**: 既存のプロジェクト操作（作成、更新、削除、一覧取得）に影響がないことを確認しました。

### 抜け穴の検証
- 脚本アップロードによる後からの公開設定変更 (`process_script_upload`) についてもコードを確認し、変更時に制限チェックが行われるため、回避不可能であることを確認しました。
