# タスク #51: PDF出力レイアウトオプション 実装計画

## 目的
台本更新時にPDF出力のA4用紙の向き（縦/横）と文字方向（縦書き/横書き）を選択できる機能を追加する。

## 現状分析
- `pdf_generator.py` の `generate_script_pdf()` は常に `landscape(A4)` + 縦書きで生成
- `CustomPageMan` クラスが縦書き用のレイアウトロジックを持つ（右→左に行が進む）
- PDFダウンロードAPIは `GET /{project_id}/{script_id}/pdf` でパラメータなし

## 設計

### 1. PDFレイアウトパターン（4種類）

| パターン | 用紙向き | 文字方向 | 用途 |
|---------|---------|---------|------|
| landscape-vertical | 横置き | 縦書き | 演劇台本の標準形式（現在のデフォルト） |
| portrait-vertical | 縦置き | 縦書き | 小説風のレイアウト |
| landscape-horizontal | 横置き | 横書き | プレゼン風レイアウト |
| portrait-horizontal | 縦置き | 横書き | 一般的な横書き文書 |

### 2. バックエンド変更

#### pdf_generator.py
- `HorizontalPageMan` クラスを新規作成
  - 横書き用のレイアウト（左→右に文字が進み、上→下に行が進む）
  - `draw_title`, `draw_author`, `draw_dialogue` 等の横書き版メソッド
- `generate_script_pdf()` にパラメータ追加:
  - `orientation`: `"landscape"` | `"portrait"` (デフォルト: `"landscape"`)
  - `writing_direction`: `"vertical"` | `"horizontal"` (デフォルト: `"vertical"`)

#### scripts.py (API)
- `download_script_pdf()` にクエリパラメータ追加:
  - `orientation: str = Query("landscape")`
  - `writing_direction: str = Query("vertical")`

### 3. フロントエンド変更

#### scripts.ts (API)
- `downloadScriptPdf()` にオプションパラメータ追加

#### ScriptDetailPage.tsx / ScriptListPage.tsx
- PDFダウンロードボタンの横にオプション選択ドロップダウンを追加
  - 用紙向き選択: 横置き / 縦置き
  - 文字方向選択: 縦書き / 横書き

### 4. 翻訳対応
5言語（日本語、英語、韓国語、簡体字、繁体字）の翻訳ファイルを更新

## DBスキーマ変更
**なし** - PDFレイアウト設定はダウンロード時のオプションとして処理し、DBに保存しない。

## テスト
- `test_pdf_generator.py` のテストケースを4パターン分に拡張
