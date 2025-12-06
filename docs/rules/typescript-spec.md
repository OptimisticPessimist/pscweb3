# TypeScript & React Coding Standards

## 1. 基本原則 (Basic Principles)
- **Strict Mode**: `tsconfig.json` で `strict: true` を必須とする。
- **No Any**: `any` 型の使用は原則禁止。必要な場合は `unknown` を使用し、適切な型ガードを行う。
- **Functional Components**: クラスコンポーネントは使用せず、すべて関数コンポーネント + Hooksで実装する。

## 2. 型定義 (Type Definitions)
- **Props**: コンポーネントのPropsは `type` ではなく `interface` を使用する（拡張性のため）。
- **Export**: 型定義は `export type` / `export interface` で明示的にエクスポートする。
- **Zod**: APIレスポンスやフォームのバリデーションには `zod` を使用し、型推論を活用する。

## 3. コンポーネント実装 (Component Implementation)
- **Named Exports**: デバッグ時の追跡容易性のため、`default export` ではなく `Named export` を使用する。
  ```tsx
  // Good
  export const MyComponent = () => { ... }
  ```
- **File Structure**: コンポーネントは `features/` または `components/` 配下に配置し、関連ファイル（テスト、型）をコロケーション（同居）させる。

## 4. スタイリング (Styling)
- **TailwindCSS**: スタイリングはTailwindCSSのユーティリティクラスを使用する。
- **clsx / twMerge**: 条件付きクラスやクラスの結合には `clsx` または `tailwind-merge` を使用する。
- **Magic Numbers禁止**: 色やspacingはTailwindのconfig（トークン）を使用し、ハードコードしない。

## 5. 状態管理 (State Management)
- **Server State**: APIデータは `TanStack Query (React Query)` で管理する。`useEffect` でのデータフェッチは避ける。
- **Client State**: グローバルなUI状態（テーマ、モーダルなど）は `Context API` または `Zustand` を使用する。

## 6. 非同期処理 & エラーハンドリング (Async & Error Handling)
- **Async/Await**: Promiseチェーンではなく `async/await` を使用する。
- **Error Boundary**: 予期せぬエラーでアプリ全体がクラッシュしないよう、Error Boundaryを設置する。

## 7. テスト戦略 (Testing Strategy)
フロントエンド開発においては、過度なテスト負担を避けつつ品質を保つため、対象の性質に応じた「ハイブリッド戦略」を採用する。

### 7.1 ロジック層 (Unit/Hook Testing)
- **対象**: `hooks/` (カスタムフック), `utils/` (ユーティリティ関数), APIクライアント
- **ツール**: **Vitest** (+ React Testing Library)
- **方針**: **TDD推奨**。状態遷移やデータ加工などのビジネスロジックは、実装前にテストケースを作成し、ロジックの正当性を担保する。

### 7.2 UIコンポーネント層 (Component/Integration Testing)
- **対象**: `components/` (ボタン, 入力フォーム), 各ページコンポーネント
- **ツール**: ブラウザプレビュー, (Optional: Storybook)
- **方針**: **実装優先**。UIの見た目や微細な挙動の変更コストを抑えるため、厳密なTDDは必須としない。
- **例外**: 複雑なバリデーションやインタラクションを持つ重要コンポーネントのみ、React Testing Libraryでの結合テストを作成する。

### 7.3 重要フロー (E2E Testing)
- **対象**: ログイン、プロジェクト作成、脚本アップロードなどの基幹機能
- **ツール**: **Playwright** (後日導入)
- **方針**: ユーザーの操作フロー全体が機能することを最終防衛ラインとして保証する。
