# タスクリスト: 脚本再アップロード後の日程調整シーン表示不具合の修正

## 状況調査
- [x] データベースモデル (`models.py`) の関連性の確認
- [x] `schedule_poll_service.py` の調査（シーン取得・分析ロジック）
- [x] `script_processor.py` および `scene_chart_generator.py` の調査（再アップロード時のデータ処理）

## 原因特定
- [x] `SchedulePollService` が「配役されていないキャラクター」がいるシーンを「稽古不可」として除外している可能性の確認
- [x] `SchedulePollService` が「キャラクターが1人もいないシーン」を分析から完全にスキップしている箇所の特定

## 修正作業
- [x] バックエンド: `SchedulePollService` の修正
  - [x] 配役（`CharacterCasting`）が存在しないキャラクターは、可用性チェックの対象から外す（無視する）ように変更
  - [x] キャラクターが設定されていないシーンも、分析結果（`possible_scenes`）に含めるように変更（「全員揃っています」扱い）
  - [x] `all_scenes` および分析結果内でのシーンのソート順を `act_number`, `scene_number` の順に修正


- [x] バックエンド: `script_processor.py` / `fountain_parser.py` の確認（必要に応じて）
  - [x] 再アップロード時に香盤表（`SceneCharacterMapping`）が正しく生成されているか確認


## 検証
- [x] ユニットテストの作成/実行
  - [x] 脚本更新後に既存の日程調整が正しく最新のシーンを分析できるか
- [x] 手動検証
  - [x] 脚本を再アップロードし、日程調整カレンダーでシーンが表示されることを確認

## 修正内容 (追加要件)
- [x] バックエンド: `SchedulePollService` の更なる修正
  - [x] 稽古可能シーン（`possible_scenes`）およびリーチ（`reach_scenes`）からあらすじ（シーン番号0以下）を確実に除外
  - [x] `get_recommendations` の分析ロジックをダブルキャスト対応（1人でもOK）に修正
  - [x] 未配役キャラクターがいる場合の判定の適正化（稽古可能からは外す）
  - [x] 全てのシーン表示を `{Act}-{Scene}: {heading}` 形式に変更

## 検証 (追加分)
- [x] ユニットテストの修正・実行（`test_schedule_poll_service_analysis_refined.py`）
- [x] 手動検証
  - [x] 日程調整画面でおすすめ日程のシーン名が正しい形式であることを確認
  - [x] 役者が揃っていないシーンが稽古可能に含まれていないことを確認




