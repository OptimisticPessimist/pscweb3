# Act-Scene採番機能 実装の確認

## 概要
台本の採番をAct（幕）ごとにSceneを1から振り直すように修正し、日程調整などのシーン選択画面で `{Act}-{Scene}` という形式で表示する機能を実装しました。

## 実装内容

### バックエンド (Fountain Parser & 通知)
1. **Scene採番ロジックの修正**
   - `fountain_parser.py` において、新しいAct（幕）が検出された際に `scene_number` を0にリセットする処理を追加しました。
   - これにより、Act 1のScene 1, 2、Act 2のScene 1, 2といった形でシーンが採番されるようになりました。

2. **通知フォーマットの修正**
   - `api/rehearsals.py` と `api/schedule_polls.py` を修正し、稽古の追加・更新、出欠確認、および日程調整確定時のDiscord通知やDiscord用イベントのタイトルに、シーン情報を `{Act}-{Scene}` （Actがない場合は `{Scene}`）の形式で含めるようにしました。

3. **テストの追加**
   - `test_fountain_parser.py` に、複数のActをまたぐテストデータを追加し、シーン番号が正しくリセットされることを検証するテストケースを追加しました。テストは全てパスしています。

### フロントエンド (表示フォーマットの統一)
1. **フォーマットユーティリティの作成**
   - `sceneFormatter.ts` を新規作成し、`actNumber` と `sceneNumber` を受け取り適切なフォーマットで文字列を返すユーティリティ関数 `formatSceneNumber` を実装しました。

2. **UIコンポーネントの修正**
   - 以下の画面/コンポーネントにおいて、`formatSceneNumber` を使用してシーン番号が `{Act}-{Scene}` 形式で一貫して表示されるように修正しました。
     - 稽古予定の作成・編集モーダル (`RehearsalModal.tsx`)
     - 日程調整の詳細画面およびカレンダービュー (`SchedulePollDetailPage.tsx`, `SchedulePollCalendar.tsx`)
     - 公開・非公開台本の詳細画面・プレビュー (`ScriptDetailPage.tsx`, `PublicScriptPage.tsx`, `PublicScriptDetailPage.tsx`)
     - 香盤表 (`SceneChartPage.tsx`)

## テスト・検証結果
- **バックエンドテスト**: 追加したパーサーのテストを含め、全てのテストがパスすることを確認しました (`pytest`)。
- **フロントエンドビルド**: TypeScriptの型エラーやビルドエラーが発生しないことを確認しました (`npm run build`)。
- **UIの確認**: 各種画面でシーンが `1-1`, `2-1` のように意図した通りのフォーマットで表示されることを確認しました。
