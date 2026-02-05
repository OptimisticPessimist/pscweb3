# メタタグのnote表示機能の実装計画

Fountain脚本のメタデータに含まれる「note」の内容を、公開設定された脚本の詳細ページおよび一覧ページで表示するようにします。

## 変更内容

### バックエンド

バックエンド側（Python/FastAPI）では既に `Script.notes` フィールドが存在し、Fountainパース時にデータが保存され、APIレスポンスにも含まれています。そのため、バックエンドの修正は不要です。

### フロントエンド

#### [MODIFY] [PublicScriptDetailPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/public_scripts/pages/PublicScriptDetailPage.tsx)
- 脚本詳細ページにおいて、使用条件や連絡先と同様に「メモ（Notes）」を表示するセクションを追加します。

#### [MODIFY] [PublicScriptsPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/public_scripts/pages/PublicScriptsPage.tsx)
- 脚本一覧ページの各カードにおいて、著者名の下に `notes` の内容を一部（三点リーダーなどで省略して）表示するようにします。

## 確認事項
- [ ] 公開設定された脚本の「note」が詳細ページに表示されること。
- [ ] 公開設定された脚本の「note」が一覧ページに（簡略化して）表示されること。
- [ ] 各言語（日本語、英語、韓国語、中国語）で適切にラベル（「メモ」、「Notes」など）が表示されること。

## 検証方法
1. `note` メタデータを含むFountainファイルをアップロードする。
2. 脚本を「公開」に設定する。
3. 公開脚本一覧（`/public-scripts`）にアクセスし、表示を確認する。
4. 公開脚本詳細（`/public-scripts/{id}`）にアクセスし、表示を確認する。
