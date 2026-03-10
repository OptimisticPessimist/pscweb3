# タスクリスト: 脚本あらすじ欠落の修正

## 1. 調査と再現
- [x] 現状のコード（fountain_parser.py）の解析
- [x] Fountainパーサーが「あらすじ（Synopsis）」要素を無視していることを特定
- [x] `collecting_description` のロジックの不備（Action要素でも即座に収集が止まる）を特定

## 2. バックエンド修正
- [ ] `backend/src/services/fountain_parser.py` の修正
    - [ ] `Synopsis`, `Parenthetical`, `Transition`, `Centered Text` 要素を処理対象に追加
    - [ ] `collecting_description` のロジック修正（最初のセクションが終わるまで収集を継続、または適切に全行を収集）
    - [ ] 欠落していた要素を `Line` モデルとして追加

## 3. 検証
- [ ] 修正後のパーサーでのパース結果の確認
- [ ] ユニットテストの実行

## 4. ドキュメント作成とマージ
- [ ] `Walkthrough.md` の作成
- [ ] ブランチのマージ
