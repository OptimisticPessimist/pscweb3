# 脚本タイトル・著者抽出タスク

- [x] 既存の脚本アップロードと解析ロジックの調査 <!-- id: 0 -->
- [ ] Fountainファイルからのタイトルと著者の抽出ロジック設計 <!-- id: 1 -->
- [x] 実装計画の作成（日本語化対応中） <!-- id: 2 -->
- [/] Backend: `scripts` テーブルに `author` カラムを追加するマイグレーション作成 <!-- id: 3 -->
- [/] Backend: `src/db/models.py` の `Script` モデル更新 <!-- id: 4 -->
- [x] Backend: `src/schemas/script.py` を更新し `author` を含める <!-- id: 5 -->
- [x] Backend: `src/services/fountain_parser.py` を更新しメタデータを抽出する（フロントエンド抽出方針に変更） <!-- id: 6 -->
- [x] Backend: `src/services/script_processor.py` を更新し `author` を保存する <!-- id: 7 -->
- [x] Backend: `src/api/scripts.py` を更新し `author` 入力を受け付ける <!-- id: 8 -->
- [x] Frontend: `ScriptUploadPage.tsx` を更新しファイル内容からメタデータを抽出・プレフィルする <!-- id: 9 -->
- [x] Frontend: `ScriptUploadPage.tsx` UIを更新しAuthorフィールドを表示・編集可能にする <!-- id: 10 -->
- [x] Backend: Discord通知を更新しAuthorを含める <!-- id: 11 -->
- [ ] 機能検証（脚本アップロード、DB確認、UI確認、通知確認） <!-- id: 12 -->
