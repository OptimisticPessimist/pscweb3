# 日程調整未回答人数の表示修正

## [Goal Description]
日程調整の未回答者に対するリマインド機能において、「{{count}}名にリマインドを送信」と変数がそのまま表示されてしまい、何人未回答かどうかがユーザーに伝わらないバグを修正します。また、未回答者の実数がより直感的にわかるようにUIを改善します。

## Proposed Changes

### Frontend Translations
- 全言語の `translation.json` で、i18nextの補間子設定（`{` と `}`）に合わせて `{{count}}` や `{{items}}` を `{count}` 等に修正します。

#### [MODIFY] ja/translation.json
#### [MODIFY] en/translation.json
#### [MODIFY] ko/translation.json
#### [MODIFY] zh-Hans/translation.json
#### [MODIFY] zh-Hant/translation.json

### Frontend UI
- `SchedulePollDetailPage.tsx` で、未回答メンバーのリマインドセクションの見出しに「未回答メンバーのリマインド ({unansweredMembers.length}名)」のように全体の人数を表示するよう修正します。

#### [MODIFY] SchedulePollDetailPage.tsx
