# Mobile Optimization Implementation Plan

## Goal Description
スマホ表示（レスポンシブデザイン）に対応させる。現状のサイドバー固定レイアウトではモバイル端末での閲覧・操作が困難なため、ハンバーガーメニューによる開閉式のサイドバーを導入する。

## User Review Required
> [!IMPORTANT]
> `AppLayout.tsx`, `Sidebar.tsx`, `Header.tsx` の構造を変更します。モバイル（画面幅 768px未満）ではサイドバーがデフォルトで非表示になり、ヘッダーのボタンで開閉するドロワー形式になります。

## Proposed Changes

### Frontend Layout

#### [MODIFY] [AppLayout.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/layouts/AppLayout.tsx)
- サイドバーの開閉状態（`isSidebarOpen`）を管理するStateを追加。
- モバイル時にサイドバーの表示を制御するロジックを追加。
- `Header` にサイドバー切り替え関数を渡す。

#### [MODIFY] [Header.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/components/layout/Header.tsx)
- `lucide-react` の `Menu` アイコンを使用したハンバーガーメニューを追加。
- `md:hidden` クラスを付与し、PC表示時は非表示にする。

#### [MODIFY] [Sidebar.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/components/layout/Sidebar.tsx)
- モバイル表示用のスタイル（`fixed`, `z-index`, `transform`）を追加。
- 背景クリックで閉じるためのオーバーレイ（バックドロップ）を追加。

### Global Styles
#### [MODIFY] [App.css](file:///f:/src/PythonProject/pscweb3-1/frontend/src/App.css)
- モバイルレイアウトに干渉する可能性のある `#root` の `padding` や `max-width` などのスタイルを見直し、必要に応じて削除またはメディアクエリで調整する。

## Verification Plan

### Manual Verification
- ブラウザの開発者ツールで画面幅をスマホサイズ（例: iPhone SE, Pixel 7）に変更して確認。
- ハンバーガーメニューが表示されること。
- メニュータップでサイドバーがアニメーションして表示されること。
- 背景タップでサイドバーが閉じること。
- PCサイズ（> 768px）に戻した際、通常のサイドバー表示に戻ること。
