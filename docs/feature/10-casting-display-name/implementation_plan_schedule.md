# スケジュール機能でのスクリーンネーム表示

## 目的
スケジュール（Rehearsal）機能において、参加者およびキャストの表示に、設定されている場合はスクリーンネーム（`display_name`）を優先して表示するように変更します。

## 変更内容

### Backend
#### [MODIFY] [rehearsal.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/rehearsal.py)
- `RehearsalParticipantResponse` に `display_name: str | None` を追加。
- `RehearsalCastResponse` に `display_name: str | None` を追加。

#### [MODIFY] [rehearsals.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/rehearsals.py)
- `get_rehearsal_schedule` において、`ProjectMember` から `display_name` マップを作成し、レスポンスに含める。
- `RehearsalResponse` を構築する箇所すべて（追加・更新時も含む）で `display_name` を設定する。

### Frontend
#### [MODIFY] [index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/types/index.ts)
- `RehearsalParticipant` インターフェースに `display_name?: string` を追加。
- `RehearsalCast` インターフェースに `display_name?: string` を追加。

#### [MODIFY] [RehearsalModal.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule/components/RehearsalModal.tsx)
- キャストタブでのユーザー選択ドロップダウンやリスト表示で `display_name` を優先表示。
- 参加者タブでのユーザー選択ドロップダウンやリスト表示で `display_name` を優先表示。

#### [MODIFY] [RehearsalParticipants.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule/components/RehearsalParticipants.tsx)
- 参加者一覧表示で `display_name` を優先表示。

## 検証計画
### 手動検証
1. スケジュールページを開く。
2. 既存のスケジュールで、メンバー名がスクリーンネーム（設定されていれば）になっていることを確認。
3. 稽古追加・編集モーダルを開き、ドロップダウンリストでスクリーンネームが表示されることを確認。
4. 参加者を追加シて、リスト上でスクリーンネームが表示されることを確認。
