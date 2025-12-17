# コードレビュー結果

## 1. 概要
- **対象ファイル**: `backend/src/api/rehearsals.py`
- **総合評価**: 3/5
- **要約**: バグ自体は修正されましたが、レスポンス構築ロジック（参加者やキャストの整形）が複数のエンドポイント（`get`, `add`, `update`）で重複しており、保守性が低くなっています。今回のバグもこの重複コードの一部が不正な状態だったことが原因です。

## 2. 詳細レビュー
| 観点 | 評価 | コメント |
| :--- | :--- | :--- |
| 命名の適切さ | OK | 変数名や関数名は分かりやすく適切です。 |
| 変数の粒度 | OK | 適切なスコープで定義されています。 |
| メソッド・関数の粒度 | WARN | `update_rehearsal` などが肥大化しています。特にレスポンス生成処理が長すぎます。 |
| 冗長性の排除 | NG | `participants` と `casts` のリストを作成するロジックが3回以上コピーペーストされています。 |
| 条件式の単純さ | OK | 複雑すぎる条件分岐はありませんが、デフォルトキャストのロジックは少し込み入っています。 |
| セキュリティ | OK | プロジェクトメンバーの権限チェック（viewer除外など）は行われています。 |
| 可読性 | WARN | 重複コードによりファイルが長くなり、全体の見通しが悪くなっています。 |

## 3. 具体的な指摘事項と修正案

#### [backend/src/api/rehearsals.py] 重複したレスポンス構築ロジック
**問題点**:
`Rehearsal` オブジェクトから `RehearsalResponse` を作成するロジック（特に `participants` と `casts` の変換、および `display_name` のマッピング）が、`get_rehearsal_schedule`, `add_rehearsal`, `update_rehearsal` の各関数内にベタ書きされており、重複しています。

**修正案**:
レスポンス変換ロジックを別関数（ヘルパーまたはサービスメソッド）に切り出すべきです。

```python
# 修正案のイメージ (src/services/rehearsal_service.py などに配置、または同ファイル内のprivate関数)

def build_rehearsal_response(
    rehearsal: Rehearsal, 
    display_name_map: dict[UUID, str]
) -> RehearsalResponse:
    
    # 参加者リスト構築
    participants_response = []
    for p in rehearsal.participants:
        user_name = "Unknown"
        if p.user:
            user_name = p.user.discord_username
        
        participants_response.append(
            RehearsalParticipantResponse(
                user_id=p.user_id,
                user_name=user_name,
                display_name=display_name_map.get(p.user_id),
                staff_role=p.staff_role
            )
        )

    # キャストリスト構築
    casts_response_list = []
    
    # 明示的なキャスト
    for rc in rehearsal.casts:
        user_name = "Unknown"
        if rc.user:
            user_name = rc.user.discord_username

        casts_response_list.append(RehearsalCastResponse(
            character_id=rc.character_id,
            character_name=rc.character.name,
            user_id=rc.user_id,
            user_name=user_name,
            display_name=display_name_map.get(rc.user_id)
        ))
        
    # デフォルトキャスト（シーン情報がある場合）
    if rehearsal.scenes: # または rehearsal.scene_id
        # ... (デフォルトキャスト計算ロジック) ...
        pass

    # ... その他のフィールド設定 ...

    return RehearsalResponse(
        id=rehearsal.id,
        # ...
        participants=participants_response,
        casts=casts_response_list
    )
```

**メリット/デメリット**:
- **メリット**: コードの重複がなくなり、ロジックが一箇所に集約されるため、今回のようなコピペミスによるバグを防げます。ファイルサイズも削減され可読性が向上します。
- **デメリット**: 既存コードの広範囲なリファクタリングが必要となり、一時的に修正コストがかかります。

## 4. 改善提案
今回の修正フェーズではバグ修正を優先しましたが、次のステップとして `api/rehearsals.py` のリファクタリング（特にレスポンス変換処理の共通化）を強く推奨します。
