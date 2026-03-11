# 脚本ビューアーの表示順序変更 実装計画

脚本ビューアーにおいて、あらすじ（シーン番号0）を登場人物リストの前に表示するように順序を変更します。

## 概要
現在、あらすじは「脚本内容」セクションの最初のシーンとして表示されていますが、これを独立したセクションとして「登場人物」の前に移動します。

## 変更内容

### [Component] Frontend (Scripts)

#### [MODIFY] [ScriptDetailPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/ScriptDetailPage.tsx)
- `script.scenes` から `scene_number === 0` のシーンを抽出します。
- 抽出したシーンを「あらすじ」セクションとして、メタデータセクションの後、登場人物セクションの前にレンダリングします。
- 「脚本内容」セクションのレンダリング対象から、あらすじシーンを除外します。

#### [MODIFY] [PublicScriptPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/PublicScriptPage.tsx)
- `ScriptDetailPage.tsx` と同様の変更を行います。

#### [MODIFY] [translation.json](file:///f:/src/PythonProject/pscweb3-1/frontend/src/locales/ja/translation.json) (および他言語)
- `script.synopsis` キーを追加しました（実施済み）。

## 検証プラン

### 手動確認
1. あらすじ（シーン0）を含む脚本を表示し、以下の順序で表示されることを確認する：
   - メタデータ（あれば）
   - **あらすじ** (新規)
   - 登場人物
   - 脚本内容（シーン1以降）
2. あらすじがない脚本を表示し、「あらすじ」セクションが表示されない、かつ通常通り動作することを確認する。
3. 言語を切り替えて、「あらすじ」のタイトルが正しく翻訳されることを確認する。
