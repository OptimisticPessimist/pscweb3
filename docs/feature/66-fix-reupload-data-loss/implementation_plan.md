# 実装計画 - 脚本再アップロード時のデータ紐付け復元

## 現状の動作
1. 脚本がアップロードされる。
2. 既存の `Character`, `Scene`, `CharacterCasting`, `RehearsalScene` などをすべて削除する。
3. Fountainファイルをパースして、新しい `Character`, `Scene` を作成する。
4. この結果、ユーザーによる手動設定が必要な「配役（誰がどの役か）」や「稽古内容（どの稽古でどのシーンをやるか）」がすべてリセットされてしまう。

## 修正方針
削除前にデータを収集し、再作成後にマッチングを行って復元する。

### 1. データの退避 (Collection)
`script_processor.py` の `process_script_upload` 内で、`cleanup_related_data` を呼ぶ前に以下の情報を取得する。

- **配役データ**: `(character_name, user_id, cast_name)` のリスト
- **稽古-シーン紐付けデータ**: `(rehearsal_id, scene_heading, act_number, scene_number)` のリスト
  - 見出し（heading）の一致を優先。Act/Scene番号の一致はサブとして使用。

### 2. データの復元 (Restoration)
`parse_and_save_fountain` が完了し、新しい `Character` と `Scene` が DB に保存された後に以下を行う。

- **配役の復元**:
  - 新しい `Character` を取得。
  - キャラクター名が一致するものに対して、退避した `(user_id, cast_name)` を使って `CharacterCasting` を作成。
- **稽古-シーン紐付けの復元**:
  - 新しい `Scene` を取得。
  - `scene.heading`（または番号）が一致するものに対して、`RehearsalScene` を再作成。
  - `Rehearsal.scene_id` (古い1対1のリレーション用) も更新。

## 変更対象ファイル
- `backend/src/services/script_processor.py`: メインのロジック変更
- `backend/src/services/scene_chart_generator.py`: `scene_number=0` の扱いの見直し

## 考慮事項
- **キャラクター名の変更**: 名前が変わった場合は自動復元できないが、それは許容範囲とする。
- **シーン見出しの変更**: 同上。
- **パフォーマンス**: 大規模な脚本でも数秒以内に終わるようにバルクインサート等を検討する。
