# 出欠確認締切の制限計画

Azure FunctionsのTimer Triggerによる効率的なポーリングを実現し、無料枠のDB負荷を軽減するため、出欠確認の回答期限を30分単位（例: 10:00, 10:30）に制限します。

## ユーザーレビューが必要な事項

> [!IMPORTANT]
> この変更により、有効な締切時刻は毎時00分または30分（XX:00 または XX:30）に強制されます。
> 既存の締切には影響しませんが、新規作成や更新時には検証が行われます。

## 変更案

### フロントエンド
#### [MODIFY] [RehearsalModal.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule/components/RehearsalModal.tsx)
- `attendance_deadline` の入力欄に `step="1800"`（30分）を設定します。
- ブラウザで手入力が可能な場合に備え、`onBlur` または `onChange` で最も近い30分単位の時刻に補正するロジックを追加します。
- 30分単位でない場合にバリデーションエラーを表示するようにします。

### バックエンド
#### [MODIFY] [rehearsal.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/rehearsal.py)
- `RehearsalCreate` スキーマの `attendance_deadline` にPydanticバリデーターを追加します。
- 分が `0` または `30` であり、秒・マイクロ秒が `0` であることを保証します。

## 検証計画

### 自動テスト
- バックエンドのテストを実行し、`RehearsalCreate` のバリデーションが機能することを確認します。
- `tests/unit/test_schemas_rehearsal.py`（存在する場合）または `tests/unit/test_api_rehearsals.py` に、有効および無効な締切時刻を確認する新しいテストケースを作成します。

### 手動検証
1. 稽古作成モーダルを開きます。
2. 「出欠確認を送信」にチェックを入れます。
3. `10:15` のような締切を設定してみます。
4. `10:00` または `10:30` に補正されるか、エラーが表示されることを確認します（UX向上のため補正を推奨）。
5. 送信し、バックエンドが有効な `10:00` または `10:30` を受け入れることを確認します。
6. API経由で `10:15` を送信した場合（フロントエンドを回避した場合）、バックエンドが拒否することを確認します。
