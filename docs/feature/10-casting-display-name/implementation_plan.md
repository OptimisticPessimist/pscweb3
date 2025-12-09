# キャスティングUIでのスクリーンネーム表示

## 目的
キャスティング画面（Add Castドロップダウンおよび配役済みリスト）において、ユーザー名（`discord_username`）の代わりに、設定されている場合はスクリーンネーム（`display_name`）を表示するようにします。

## 変更内容

### Backend
#### [MODIFY] [character.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/character.py)
- `CastingUser` スキーマに `display_name: str | None` フィールドを追加します。

#### [MODIFY] [characters.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/characters.py)
- `list_project_characters` で `ProjectMember` を取得し、ユーザーIDから表示名へのマッピングを作成してレスポンスに含めます。
- `add_casting` および `remove_casting` において、レスポンス作成時に `ProjectMember` を参照して表示名を含めます。

### Frontend
#### [MODIFY] [index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/types/index.ts)
- `CastingUser` インターフェースに `display_name?: string` を追加します。

#### [MODIFY] [CastingPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/casting/pages/CastingPage.tsx)
- "Assign Cast" モーダルのドロップダウンで `{member.display_name || member.discord_username}` を表示するように変更します。
- 配役済みリストの表示で `{cast.display_name || cast.discord_username}` を表示するように変更します。

## 検証計画
### 手動検証
1. キャスティングページを開く。
2. "Add Cast" ボタンを押してモーダルを開く。
3. ドロップダウンリストで、表示名が設定されているメンバーがその名前で表示されることを確認する。
4. キャストを割り当てる。
5. 割り当て後のリスト表示でも表示名が使われていることを確認する。
