# 未使用変数の修正とタイトル自動入力の改善

`ScriptUploadPage.tsx` において、ファイルから抽出されたタイトル (`extractedTitle`) が定義されているものの使用されていないため、TypeScript のビルドエラー (`TS6133`) が発生しています。
この変数を適切に使用することで、エラーを解消し、ユーザー体験を向上させます。

## 変更内容

### Frontend

#### [MODIFY] [ScriptUploadPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/ScriptUploadPage.tsx)

- `onDrop` 関数内で、`extractedTitle` を使用してタイトルの初期値を設定するように変更します。
- 優先順位: 抽出されたタイトル > ファイル名（拡張子抜き）

```tsx
// 修正イメージ
if (!title) {
    setTitle(extractedTitle || uploadedFile.name.replace(/\.fountain$/i, ''));
}
```

## 検証計画

### 自動テスト
- `frontend` ディレクトリ配下で `npm run build` (内部で `tsc -b` を実行) を行い、コンパイルエラーが解消されることを確認します。

### 手動確認
- ブラウザでスクリプトアップロード画面を開き、タイトルが記述された Fountain ファイルをドロップした際に、そのタイトルが自動入力されることを確認します。
