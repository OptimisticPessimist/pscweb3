# 公開脚本プロジェクトの制限除外

## 概要
現在、ユーザーがオーナーとして作成できるプロジェクト数は最大2つに制限されている。
この制限の計算において、「脚本が公開設定になっているプロジェクト」を含めないように変更する。
これにより、公開脚本を含むプロジェクトは事実上無制限に作成可能（または別枠）となり、プライベートなプロジェクトのみが2つまでの制限を受けることになる。

## 前提条件
- 「公開脚本プロジェクト」の定義: `is_public=True` の `Script` を1つ以上含むプロジェクト。
- 制限対象: `is_public=True` の `Script` を**含まない**プロジェクトのオーナー数が2未満であること。

## 変更内容

### Backend
#### `backend/src/api/projects.py`
- `create_project` API
    - 現在: 単純に `ProjectMember` テーブルから `role='owner'` のレコード数をカウントしている。
    - 変更後:
        1. ユーザーがオーナーの全プロジェクトを取得。
        2. 各プロジェクトについて、「公開脚本を含んでいるか」を確認。
        3. 「公開脚本を含まない」プロジェクトのみをカウント対象とする。
        4. そのカウントが2以上であれば作成を拒否する。

- `import_script` API
    - 同様のチェックロジックが存在するため、共通化または同様の修正を行う。

#### `backend/src/services/script_processor.py` (Loophole Prevention)
- `process_script_upload` (or `get_or_create_script`)
    - 脚本の更新時、`is_public` が `True` から `False` に変更される場合、または非公開のまま更新する場合に制限チェックを行う。
    - ロジック:
        1. 更新後の状態で「非公開プロジェクト」の数が制限(2つ)を超えることになるか試算する。
            - 既存プロジェクトが公開状態(Script public) -> 非公開に変更 = Non-public count + 1
            - これにより Non-public count > 2 となるならエラーにする。
    - エラーメッセージ例: "Cannot change script to private because you would exceed the limit of 2 private projects."

### Logic Details
基本ロジック（共通関数化推奨）:
```python
async def check_project_limit(user_id: UUID, db: AsyncSession, excluding_project_id: UUID | None = None) -> None:
    # ユーザーの全所有プロジェクトを取得
    owned_projects = await db.execute(...)
    
    non_public_count = 0
    for proj in owned_projects:
        # 除外対象プロジェクト（現在操作中のプロジェクトなど）は計算に含めない、
        # または「このプロジェクトが非公開になったと仮定」して計算するロジックが必要。
        # シンプルに:
        # 「現在DBにある非公開プロジェクト数」を取得
        # 新規作成時: Count >= 2 -> Error
        # 更新時(Public->Private): (Count of OTHER private projects) + 1 >= 3 -> Error (Limit is 2)
        pass # 詳細実装時に調整
```

## 検証計画
### テストケース
1. **通常制限の確認**: 公開脚本を含まないプロジェクトを2つ作成 -> 3つ目の作成がエラーになること。
2. **公開プロジェクトの除外確認**:
    - プロジェクトAを作成 (Scriptなし) -> Count 1
    - プロジェクトBを作成 (Scriptあり, is_public=True) -> Count 1 (除外)
    - プロジェクトCを作成 (Scriptなし) -> Count 2
    - プロジェクトDを作成 -> エラー (Count 2上限)
3. **公開設定変更の影響**:
    - プロジェクトA (Private) -> 公開に変更 -> Countが減る -> 新規作成が可能になること。

### 自動テスト
- `backend/tests/unit/test_api_projects.py` (もしあれば) または新規テストを作成し、上記のシナリオを検証する。
