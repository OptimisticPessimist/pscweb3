# [演劇台本の書式変更]

演劇台本の一般的な書式である「縦書きで紙は横置き」に対応するため、PDF生成時の用紙設定を変更する。

## User Review Required
特になし

## Proposed Changes
### Backend
### Backend
#### [MODIFY] [pdf_generator.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/pdf_generator.py)
- `playscript` ライブラリの `PageMan` クラスと `psc_to_pdf` 関数をベースに、カスタマイズ版を実装する。
- **表紙レイアウト変更**:
    - タイトルと著者名（全メタデータ）を表示した後、強制的に改ページを入れる処理を追加。
- **あらすじスタイル変更**:
    - `# あらすじ` (H1) セクションを検出するロジックを追加。
    - 「あらすじ」セクション内のト書き（DIRECTION）を、通常とは異なるスタイル（例：インデント変更、フォント変更など）で描画する `draw_synopsis_text` メソッドを追加して使用。
    - あらすじのスタイリングは、他の章と区別が付くように調整（ユーザー要望）。

## Verification Plan
### Automated Tests
- `backend/test_pdf_local.py` を実行し、エラーなくPDFが生成されることを確認する。
- 生成されたPDFのファイルサイズが変更されていることを確認する（用紙サイズ変更による）。

### Manual Verification
- 生成されたPDFを開き、用紙が横向きで、テキストが縦書きになっていることを確認する（※今回は環境上閲覧不可のため、コード設定値と実行ログで判断）。
