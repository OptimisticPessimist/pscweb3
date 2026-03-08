# 役割別利用マニュアルの実装

演劇の現場における役職別（制作/演出/脚本/演出助手・舞台監督/役者/テクニカルスタッフ）にタブ切り替えUIでマニュアルを表示する機能を実装する。既存の権限ベース（管理者/編集者/閲覧者）マニュアルを完全に置き換える。

## Proposed Changes

### マニュアルコンテンツ構造

現在の構造（言語ごとに1つの大きなMarkdown文字列）を、**共通セクション + 役職別セクション**に分割する。

各タブの順番と内容:

| 順番 | タブ | 推奨権限 | 主な内容 |
|:---:|:---|:---|:---|
| 1 | 🎪 制作（Producer） | 管理者 | プロジェクト作成、メンバー招待、Discord設定、マイルストーン、チケット予約管理 |
| 2 | 🎬 演出（Director） | 管理者/編集者 | キャスティング、香盤表、スケジュール管理、日程調整アンケート、出欠確認 |
| 3 | 📝 脚本（Playwright） | 編集者 | 脚本アップロード、Fountain形式、公開・共有、インポート |
| 4 | 🎭 演出助手・舞台監督（AD/SM） | 編集者 | スケジュール作成・編集、出欠催促、香盤表更新、スタッフ管理 |
| 5 | 🎤 役者（Cast） | 閲覧者 | 出欠回答、マイスケジュール、脚本閲覧、香盤表確認、日程調整回答 |
| 6 | 🔊💡 テクニカルスタッフ | 閲覧者 | スケジュール確認、出欠回答、脚本閲覧、日程調整回答 |

共通セクション（全タブの上部に常に表示）:
- ログイン方法
- ダッシュボード
- 言語切り替え
- プロジェクト作成数の制限について

---

### フロントエンド

#### [MODIFY] [ManualPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/ManualPage.tsx)

- 現在の単一Markdown表示から、**タブ切り替えUI**に変更
- タブは Headless UI の `Tab` コンポーネントを使用（既にプロジェクトに導入済み）
- 「はじめに」共通セクションをタブの上に常時表示
- 選択タブに応じた役割別コンテンツを表示
- URLクエリパラメータ (`?role=producer` など) でタブの直接リンク対応

#### [DELETE] [manualContent/ja.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/ja.ts)
#### [DELETE] [manualContent/en.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/en.ts)
#### [DELETE] [manualContent/ko.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/ko.ts)
#### [DELETE] [manualContent/zh-Hans.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/zh-Hans.ts)
#### [DELETE] [manualContent/zh-Hant.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/zh-Hant.ts)
#### [DELETE] [manualContent/index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/index.ts)

既存の言語ごと1ファイル構成を廃止。

#### [NEW] [manualContent/common/](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/common/) ディレクトリ

共通セクション（はじめに）を言語別に格納:
- `ja.ts`, `en.ts`, `ko.ts`, `zh-Hans.ts`, `zh-Hant.ts`

#### [NEW] [manualContent/roles/](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/roles/) ディレクトリ

役割別コンテンツを言語・役割別に格納:
- `producer/ja.ts`, `producer/en.ts`, ... (制作)
- `director/ja.ts`, `director/en.ts`, ... (演出)
- `playwright/ja.ts`, `playwright/en.ts`, ... (脚本)
- `ad-sm/ja.ts`, `ad-sm/en.ts`, ... (演出助手・舞台監督)
- `cast/ja.ts`, `cast/en.ts`, ... (役者)
- `tech-staff/ja.ts`, `tech-staff/en.ts`, ... (テクニカルスタッフ)

#### [MODIFY] [manualContent/index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/pages/manualContent/index.ts)

新しい構造に合わせてエクスポートを更新。型定義とヘルパー関数を追加。

```typescript
// 役割の型定義
export type ManualRole = 'producer' | 'director' | 'playwright' | 'ad-sm' | 'cast' | 'tech-staff';

// 役割の順番定義
export const MANUAL_ROLES: ManualRole[] = [
  'producer', 'director', 'playwright', 'ad-sm', 'cast', 'tech-staff'
];

// 共通コンテンツ取得関数
export function getCommonContent(lang: string): string;

// 役割別コンテンツ取得関数
export function getRoleContent(role: ManualRole, lang: string): string;
```

---

### i18n（翻訳キー）

#### [MODIFY] 各言語の translation.json

`manual` セクションにタブラベル用のキーを追加:

```json
{
  "manual": {
    "title": "利用マニュアル",
    "selectRole": "あなたの役職を選んでください",
    "roles": {
      "producer": "制作",
      "director": "演出",
      "playwright": "脚本",
      "adSm": "演出助手・舞台監督",
      "cast": "役者",
      "techStaff": "テクニカルスタッフ"
    },
    "recommendedPermission": "推奨権限",
    "permissions": {
      "owner": "管理者",
      "editor": "編集者",
      "viewer": "閲覧者"
    }
  }
}
```

---

## Verification Plan

### ビルド確認
```powershell
cd f:\src\PythonProject\pscweb3-1\frontend
npm run build
```
TypeScriptコンパイルが通ること、ビルドエラーがないことを確認。

### ブラウザ確認（手動テスト）
1. `npm run dev` でフロントエンドを起動
2. `/manual` にアクセス
3. 以下を確認:
   - 共通セクション（はじめに）が上部に表示される
   - 6つのタブが表示される（制作/演出/脚本/演出助手・舞台監督/役者/テクニカルスタッフ）
   - 各タブをクリックすると対応するコンテンツが表示される
   - 言語切替で全タブのコンテンツが切り替わる
   - URLクエリパラメータ `?role=producer` 等でタブが直接選択される
   - モバイル幅でタブが適切に折り返し or スクロール表示される
