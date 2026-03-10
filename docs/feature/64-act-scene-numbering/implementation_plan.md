# Act毎のScene番号振り直し機能の実装計画

台本の採番をAct（幕）ごとにSceneを1から振り直すように修正し、日程調整などでSceneを選択する際に `{Act}-{Scene}` という形式で表示するための実装計画です。

## User Review Required
この変更により、既存の台本データについて、Actが設定されている場合はシーン番号が上書きされる形になります。
データベースに保存されている既存データのマイグレーション（すでにあるシーンの番号を振り直すバッチ処理など）は今回はスコープ外とし、今後アップロード・更新される台本から適用される想定で進めます（既存の台本も「更新」すれば再パースされて適用されます）。問題ないかご確認ください。

## Proposed Changes

### Backend (Parser Logic & Tests)
バックエンドではFountainパーサーがシーン番号を採番しているため、ここのロジックを修正します。

#### [MODIFY] fountain_parser.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- 新しいAct（幕）が検出された際（`is_section_act` または `is_dot_act` が `True` の箇所）に、`scene_number` を `0` にリセットする処理を追加します。

#### [MODIFY] test_fountain_parser.py (file:///f:/src/PythonProject/pscweb3-1/backend/tests/unit/test_fountain_parser.py)
- 複数のActが含まれるテストデータを追加し、Actが変わったときにシーン番号が `1` からリセットされることを検証するテストケースを追加します。

#### [MODIFY] rehearsals.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/api/rehearsals.py)
- 稽古追加・更新時のDiscord通知にシーン見出しを含める際、Act番号が存在すれば `{Act}-{Scene}` 形式で表示するように修正します。
- 出欠確認イベント作成時のタイトルにシーン情報を含めます。

#### [MODIFY] schedule_polls.py (file:///f:/src/PythonProject/pscweb3-1/backend/src/api/schedule_polls.py)
- 日程調整から稽古が確定した際のDiscord通知で、確定したシーンの情報（`{Act}-{Scene}`）が含まれていないため追記します。

---

### Frontend (Formatter & UI Components)
フロントエンドではシーンを選択・表示する箇所が多岐にわたるため、共通のフォーマッターを作成して適用します。

#### [NEW] sceneFormatter.ts (file:///f:/src/PythonProject/pscweb3-1/frontend/src/utils/sceneFormatter.ts)
- `actNumber` が存在する場合は `{actNumber}-{sceneNumber}`、存在しない場合は `{sceneNumber}` の形式で文字列を返すユーティリティ関数を作成します。

#### [MODIFY] ScriptDetailPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/ScriptDetailPage.tsx)
- 台本詳細のシーン一覧表示において、シーン番号の表記をフォーマッターを使った形に変更します。

#### [MODIFY] PublicScriptPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scripts/pages/PublicScriptPage.tsx)
- 公開台本の表示におけるシーン番号の表記を変更します。

#### [MODIFY] PublicScriptDetailPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/public_scripts/pages/PublicScriptDetailPage.tsx)
- 公開台本詳細の表示におけるシーン番号の表記を変更します。

#### [MODIFY] RehearsalModal.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule/components/RehearsalModal.tsx)
- 稽古予定の作成・編集モーダルでのシーン選択チェックボックスのラベル表記を変更します。

#### [MODIFY] SceneChartPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/scene_charts/pages/SceneChartPage.tsx)
- 香盤表における表記を調整します。（現在はAct列とScene列が分かれているため、統合するかどうかを検討します）

#### [MODIFY] SchedulePollDetailPage.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule_polls/pages/SchedulePollDetailPage.tsx)
- 日程調整詳細画面内の「稽古可能なシーン」等の表記を変更します。

#### [MODIFY] SchedulePollCalendar.tsx (file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule_polls/components/SchedulePollCalendar.tsx)
- カレンダービューのシーン絞り込みプルダウンおよび、候補日程詳細パネルの表示におけるシーン番号表記を変更します。

## Verification Plan

### Automated Tests
*   `pytest backend/tests/unit/test_fountain_parser.py -v` を実行し、既存テストおよび追加したActの切り替わりテストがパスすることを確認します。
*   `cd frontend && npm run build` を実行し、TypeScriptの型エラーやビルドエラーが発生しないことを確認します。

### Manual Verification
*   各種画面（台本詳細、香盤表、日程調整の作成/カレンダー、稽古予定の作成モーダル等）で、シーンが `1-1`, `1-2`, `2-1` のように表記されていることを目視確認します。
