# 実装計画: スケジュール（日程）調整機能の実装

## 1. 概要 (Goal Description)
「調整さん」や「TONTON」のような、グループ内でのスケジュール調整機能（日程調整機能）を実装します。
既存の出欠確認（AttendanceEvent）とは別に、**どの日程を稽古等にするかを相談・決定するための機能**として独立させます。
また、Discord上で完結して候補日に対する回答（〇、△、×）を入力できるフローを実現し、UIとしてシームレスな体験を提供します。
最終的に調整結果から、既存のスケジュール（`Rehearsal`）を作成または更新できるように連携します。

## 2. ユーザーレビュー要件 (User Review Required)
> [!IMPORTANT]
> - 本機能では新規のテーブルを3つ（`SchedulePoll`, `SchedulePollCandidate`, `SchedulePollAnswer`）追加します。DBマイグレーション（alembic）が必要です。
> - Discord Interaction を使用するため、Discord Botのメッセージコンポーネント（ボタン等）のUI設計が含まれます。TONTON風にする場合、候補日時ごとにボタンを配置する必要がありますが、Discordの制約上（1メッセージあたりボタンは最大25個まで）候補日が多すぎる場合はメッセージを分割するか、セレクトメニューを利用するなどの工夫が必要です。今回は「1メッセージにつき最大25個の候補（5行×5列のボタン）」を上限とするか、UIを検討します。
>   - ※方針の提案: 「〇」「△」「×」のリアクションボタンを候補ごとに並べるのはDiscordのボタン数上限に引っかかりやすいため、**「候補日を選択するセレクトメニュー」＋「ステータス（〇/△/×）を選択するボタン群」**を組み合わせたUI、または **リアクションベースの投票** が現実的です。
>   - どちらのアプローチが良いか、ご確認ください（プランではInteractionボタン＋セレクトメニューを想定しています）。

### Discord UIの具体例（確定）

**ハイブリッド方式（常にWebリンク併記 ＋ 候補日が5日以内ならボタンも表示）** を採用します。

#### 送信されるメッセージのイメージ

```text
【日程調整】10月公演 稽古スケジュール調整
作成者: 演出太郎
（※以下のボタンから回答するか、Webフォームを開いて回答してください）

[現在の回答状況]
① 10/1(金) 19:00-: 〇(3) △(1) ×(0)
② 10/2(土) 13:00-: 〇(1) △(2) ×(1)
...
===============================
[① 10/1] [〇] [△] [×]   ← 5日程以内の場合のみ行ごとのボタンを表示
[② 10/2] [〇] [△] [×]
===============================
[🌐 Webフォームを開いて一括回答する]
===============================
```

### スケジュール最適化・優先度アルゴリズム (Priority Algorithm)
調整結果から「どの日程で・どのシーンの稽古をするべきか」を提案する機能を追加します。
特定のシーン(`Scene`)の稽古を行うには、そのシーンに登場するキャラクター(`Character`)に配役されているメンバー(`User`)の参加が**必須**となります。また、演出家などの特定のスタッフロール(`staff_role`)を持つメンバーの参加も優先されるべきです。

**アルゴリズム要件:**
1. **シーンごとの参加必須者の算出:**
   - そのシーンに登場するキャラクター(`SceneCharacterMapping`)を取得。
   - キャラクターに配役されているユーザー(`CharacterCasting`)を「必須参加者(Required Participants)」としてリストアップ。
2. **スタッフロールの優先度:**
   - プロジェクトメンバー(`ProjectMember`)のうち、`default_staff_role` に「演出」等をもつ人物を「優先参加者(Priority Participants)」として定義。
3. **候補日ごとのスコアリング (Scene Fitness Score):**
   - **必須参加者が全員「〇」または「△」であるか**をチェック。1人でも「×」がいれば、そのシーンの稽古としては不適合（スコア0）。
   - **優先参加者（演出など）の参加状況**や、全体の「〇」の数でスコアを加算し、その日に最も適したシーンを算出する。

#### スケジュール管理者（演出・制作等）の決定フロー
スケジュール管理者は**Web画面から日程を最終決定**し、既存のスケジュール機能(`Rehearsal`)への紐付けを行います。

1. **集計・レコメンドの確認**: Web上の「日程調整 詳細画面」を開くと、各候補日の回答一覧とともに、アルゴリズムが算出した**「この日はシーン◯とシーン△の稽古に最適です（全必須キャスト参加可能）」**というレコメンドが表示されます。
2. **決定とスケジュール生成**: 管理者はレコメンドを参考にチェックボックス等で日程と稽古対象シーンを選択し、「確定してスケジュールに登録」ボタンを押します。
3. **Rehearsalの自動作成**: 確定された情報をもとに、システムが自動的に `Rehearsal`（稽古予定）および紐づく `RehearsalScene`、`RehearsalCast`（参加者）をデータベースに生成します。これにより、確定した日程が既存のカレンダーやMy Scheduleに即座に反映されます。
4. **Discordへの通知**: （オプション）確定した結果がDiscordのチャンネルに「以下の日程で稽古スケジュールが確定しました」として自動通知されます。

## 3. 提案する変更 (Proposed Changes)

### データベースモデル (Database Models)
#### [MODIFY] `backend/src/db/models.py`
以下のモデルを新規追加します。
- `SchedulePoll`: 日程調整の親レコード (project_id, title, description, message_id, channel_id, creator_id, is_closed)
- `SchedulePollCandidate`: 具体的な候補日時 (poll_id, start_datetime, end_datetime)
- `SchedulePollAnswer`: 各メンバーの回答 (candidate_id, user_id, status: 'ok', 'maybe', 'ng')

### APIとスキーマ (Schemas & API)
#### [NEW] `backend/src/schemas/schedule_poll.py`
- 日程調整の作成、取得、更新用のスキーマ定義。
#### [NEW] `backend/src/api/schedule_polls.py`
- `/projects/{project_id}/polls/` エンドポイントの実装。
- 作成（Discordへの通知含む）、一覧、詳細、および**「決定（Rehearsalの生成）」**のアクション。
#### [MODIFY] `backend/src/main.py` またはルーター定義ファイル
- 新しい `schedule_polls` ルーターの登録。

### Discord連携 (Discord Integration)
#### [NEW] `backend/src/services/schedule_poll_service.py`
- スケジュール調整のビジネスロジック。
- Discordに送信するインタラクションコンポーネント（セレクトメニューやボタン）の構築。
#### [MODIFY] `backend/src/api/interactions.py`
- Discordからのボタンクリックやセレクトメニュー選択を処理するエンドポイントの拡張。
- `poll:{candidate_id}:{status}` 等の custom_id を適切に処理して `SchedulePollAnswer` に保存するロジックの追加。

### スケジュール機能との連携 (Rehearsal Integration)
#### [MODIFY] `backend/src/api/rehearsals.py` 
- SchedulePollが「決定」された際に、指定された候補日から `Rehearsal` レコード（および必要に応じて `RehearsalSchedule`）を生成する処理を連携させます。

## 4. 検証計画 (Verification Plan)

### 自動テスト (Automated Tests)
1. **Model & CRUD Tests**: `SchedulePoll` 関連のレコード作成、回答の upsert が正常に行われるかのユニットテスト。
   - `pytest backend/tests/unit/test_schedule_polls.py`
2. **Interaction Tests**: `api/interactions.py` に模擬のDiscord Interactionペイロード（日程調整の回答）をPOSTし、正しくＤBが更新され、レスポンスが返るかのインテグレーションテスト。
   - `pytest backend/tests/integration/test_discord_interactions.py`
3. **Rehearsal Creation Flow**: 日程調整の結果から `Rehearsal` が生成されることのAPI機能テスト。

### 手動検証 (Manual Verification)
1. ローカル環境起動後、Web（またはSwagger UI）から新規「日程調整」を作成する。
2. 設定したDiscordチャンネルに通知と回答用コンポーネントが送信されることを確認する。
3. Discord上で回答（〇、△、×）を行い、ボットからエフェメラルメッセージで完了通知が返ることを確認する。
4. APIを通して集計結果が正しく取得できることを確認する。
5. 集計結果をもとに、特定の日程を「稽古スケジュールとして確定」する操作を行い、DBに Rehearsal が作られることを確認する。
