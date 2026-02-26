# 日程調整カレンダー シーン絞り込み機能 バグの修正

## 課題
- シーン絞り込みのドロップダウンリストに `schedulePoll.allScenes` しか出ない（選択肢が表示されない）。
- ドロップダウンの右側の矢印（v）が二重に表示されている。

## 原因分析
- **選択肢が表示されない問題**: ドロップダウン（`<select>`）の見た目かイベントがCSSクラス（特に追加した `relative z-10`, `appearance-none`、あるいはTailwind formsプラグインの干渉）によって正しく動作していない、もしくは背面のレイヤーに隠れてしまっている可能性があります。また、`min-w-[240px]` や親の `overflow` の設定も影響している可能性があります。
- **矢印が二重になる問題**: `<select>` 要素のデフォルトの矢印スタイルを消すために `appearance-none` を指定していますが、`@tailwindcss/forms` プラグインを使用している場合、`appearance-none` よりも forms プラグインのベーススタイル（独自の矢印SVGの背景画像設定など）が勝ってしまっているか、競合している可能性があります。`bg-none` などの追加指定が必要です。

## Proposed Changes

### `frontend/src/features/schedule_polls/components/SchedulePollCalendar.tsx`
カレンダーコンポーネントの該当箇所のCSSクラスおよび構成を以下のように修正します。

#### [MODIFY] `SchedulePollCalendar.tsx`(file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/schedule_polls/components/SchedulePollCalendar.tsx)
- `select` 要素からTailwind formsプラグインのデフォルト背景画像（矢印）を消去するため、`bg-none` などのユーティリティを追加。
- ドロップダウンの選択肢がクリップされないように親要素の `z-index` 周囲のスタイルを見直し、必要以上に複雑な重なり順を避ける（`z-10` や `min-w-[240px]` など、前回追加したクラスが悪さをしている可能性が高いため、これらを整理する）。
- `pointer-events-none` などの指定が誤って `select` 自身のクリックを阻害していないか（特に Safari などの Webkit での挙動）確認し、修正する。
- 矢印が二重になるのを防ぐため、明示的に `bg-none` または `!appearance-none bg-transparent` のようにしてデフォルトの背景を取り除く。

## Verification Plan

### Manual Verification
1. フロントエンドをローカルで立ち上げ、日程調整カレンダー画面を開く。
2. シーン絞り込みのプルダウンをクリックし、すべてのシーンリストが表示されるか確認する。
3. プルダウンの右側の矢印が1つだけ（独自に配置した `ChevronLeft` のみ）になっているか確認する。
4. シーンを選択した際に、正しくフィルタリングが機能するか（前回の動作が維持されているか）確認する。
