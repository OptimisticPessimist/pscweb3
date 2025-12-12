# コードレビュー報告書 (2025-12-13)

## 1. 概要
- **対象**: プロジェクト全体 (主に `backend/src/api`, `services`, `frontend/src/features/projects`)
- **総合評価**: 4/5
- **要約**: 全体的に命名規則や構成は統一されており、可読性は高いです。特にTypeHintの活用やPydanticモデルによるバリデーションが適切に行われています。ただし、`rehearsals.py` のエンドポイント関数が肥大化しており、保守性に若干の懸念があります。また、新機能のマイルストーン設定において、UIとAPIで権限の整合性が取れていない箇所が見つかりました。

## 2. 詳細レビュー

| 観点 | 評価 | コメント |
| :--- | :--- | :--- |
| **命名の適切さ** | OK | 一貫性があり、理解しやすい命名です。 |
| **変数の粒度** | OK | 適切です。 |
| **メソッド・関数の粒度** | WARN | `rehearsals.py` 内の `add/update` 処理が非常に長く、複数の責務（DB保存、関連データ更新、通知、メンション生成）を持っています。 |
| **冗長性の排除** | OK | `AttendanceService` などの切り出しは良好です。 |
| **条件式の単純さ** | OK | 複雑なネストは少ないですが、権限チェックと条件分岐が混在している箇所があります。 |
| **セキュリティ** | WARN | マイルストーン操作に関して、APIは「編集者(Editor)」も許可していますが、UIは「オーナー(Owner)」のみに制限されています。意図的な制限でなければ、編集者も操作可能にすべきです。 |
| **可読性** | OK | コメントも適切に記載されており、読みやすいです。 |

## 3. 具体的な指摘事項と修正案

### ① [backend/src/api/rehearsals.py] 関数の肥大化
**問題点**:
`add_rehearsal` および `update_rehearsal` 関数が200行を超えており、DB操作、複雑な関連データの保存、Discord通知の構築などが混在しています。

**修正案**:
通知メッセージの構築やメンションの収集ロジックを `RehearsalService` またはヘルパー関数に切り出すことを推奨します。

```python
# 例: サービスの切り出しイメージ
async def add_rehearsal(...):
    # バリデーション
    # ...
    
    # 保存処理
    rehearsal = await rehearsal_service.create_rehearsal(db, data)
    
    # 通知処理
    await notification_service.notify_rehearsal_update(project, rehearsal, "created")
    
    return rehearsal
```

**メリット/デメリット**:
- **メリット**: コードの見通しが良くなり、テストもしやすくなります。通知ロジックの再利用性が高まります。
- **デメリット**: リファクタリングの工数が発生します。

---

### ② [frontend/.../ProjectSettingsPage.tsx] マイルストーン権限の不一致
**問題点**:
バックエンドの `create_milestone` / `delete_milestone` は `viewer` 以外（つまり `editor` も含む）のアクセスを許可していますが、フロントエンドの `MilestoneSettings` コンポーネントには `isOwner` （オーナーのみ）のフラグが渡されており、編集者がUIから操作できません。

**修正案**:
編集者も操作可能にする場合、`ProjectSettingsPage.tsx` で渡すフラグを修正します。

```tsx
// frontend/src/features/projects/pages/ProjectSettingsPage.tsx

// 修正前
<MilestoneSettings projectId={projectId!} isOwner={isOwner} />

// 修正後
const canEdit = project.role === 'owner' || project.role === 'editor';
<MilestoneSettings projectId={projectId!} isOwner={canEdit} />
// ※ Props名 `isOwner` も `canEdit` に変えるのが理想ですが、まずは値の変更のみ提案します。
```

**メリット/デメリット**:
- **メリット**: APIの設計意図（編集者もマイルストーン管理可能）とUIが一致し、利便性が向上します。
- **デメリット**: 特になし。

---

### ③ [frontend/.../MilestoneSettings.tsx] アラート表示
**問題点**:
成功・失敗のフィードバックに `alert()` を使用しています。操作のたびにブロッキングなポップアップが出るため、UXがあまり良くありません。

**推奨**:
トースト通知（Toasts）などの非同期通知UIの導入を検討してください（今回は必須ではありません）。

## 4. 改善提案 (Optional)

- **自動テストの拡充**: バックエンドのテストカバレッジを向上させ、特に複雑な `rehearsals.py` の通知ロジックなどを保護することを推奨します。
- **i18n キーの統一**: 翻訳キーが `project.settings.milestones` のように深くネストしていますが、一貫性があるため現時点では問題ありません。

以上
