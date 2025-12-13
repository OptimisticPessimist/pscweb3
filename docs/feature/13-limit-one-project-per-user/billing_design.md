# 課金によるプロジェクト数制限解除の設計案

## 結論
**DBの根本的な見直しは不要です。**
既存の `users` テーブルへのカラム追加と、いくつかの新しいテーブルの追加で対応可能です。

## 設計の詳細

### 1. データベース設計の変更 (Phase 1: シンプルなプラン管理)
最もシンプルな形として、ユーザーに「プラン」情報を付与します。

**変更点:**
- `users` テーブルに `plan` カラムを追加

```python
class User(Base):
    # ... 既存のカラム ...
    # 'free', 'pro', 'enterprise' などのEnum値、またはプランID
    plan: Mapped[str] = mapped_column(String(20), default="free") 
```

### 2. ビジネスロジックの変更 (Backend)
現在 `projects.py` に直接記述している制限ロジックを、設定可能な形に変更します。

**変更前 (Hardcoded):**
```python
if len(owned_projects) >= 2:
    raise HTTPException(...)
```

**変更後 (Configurable):**
```python
# 設定値 (定数ファイルまたは環境変数で管理)
PLAN_LIMITS = {
    "free": 2,
    "pro": 10,
    "enterprise": 999
}

# 判定ロジック
user_limit = PLAN_LIMITS.get(current_user.plan, 2)
if len(owned_projects) >= user_limit:
    raise HTTPException(...)
```

### 3. 将来的な拡張 (Phase 2: サブスクリプション管理)
実際に決済システム（Stripe等）を導入する場合、決済状態や有効期限を管理するために `subscriptions` テーブルを導入します。

**新規テーブル:**
- `Subscription`
  - `id`: UUID
  - `user_id`: ForeignKey(users.id)
  - `status`: 'active', 'canceled', 'past_due' (決済ステータス)
  - `current_period_end`: DateTime (有効期限)
  - `stripe_customer_id`: String (決済プロバイダのID)

この場合、制限判定ロジックは以下のようになります。
1. `current_user` に紐づく `Subscription` を取得
2. 有効期限内かつステータスが `active` なら `Pro` 扱い
3. それ以外なら `Free` 扱い

## 移行ステップ案

1. **現在の実装**: とりあえず全員 `Free` 扱いとして、コード内で「2つ」制限をかける（今回完了）。
2. **次のステップ**: DBに `plan` カラムを追加し、手動（管理者操作）で特定のユーザーを `Pro` に変更できるようにする。
3. **最終形**: 決済システムを組み込み、支払い完了時に自動で `plan` を更新する、または `subscriptions` テーブルを作成する。

## メリット
- 現在の `TheaterProject` や `ProjectMember` の構造を壊すことなく、ユーザー属性の追加だけで対応できます。
- アプリケーションロジックへの影響も、「作成時のチェック」箇所のみに限定されます。
