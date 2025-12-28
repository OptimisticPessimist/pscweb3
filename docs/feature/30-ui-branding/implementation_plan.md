# UIブランディング更新 実装計画

## 概要
フロントエンドのページタイトル形式を「PSCWEB3 -{PageTitle}-」に統一し、プロジェクトの一貫性を向上させます。また、Faviconの刷新案を作成します。

## 変更内容

### Frontend
- **ライブラリ追加**: `react-helmet-async`
- **コンポーネント作成**: `src/components/PageHead.tsx`
- **ページ修正**:
    - `App.tsx`: `HelmetProvider` の追加
    - `DashboardPage.tsx`: `PageHead` の適用
    - `TicketReservationPage.tsx`: `PageHead` の適用

## 検証計画
- 各ページにアクセスし、ブラウザのタブラベルが正しく変更されるか確認。
- `npm run build` が正常に完了するか確認。
