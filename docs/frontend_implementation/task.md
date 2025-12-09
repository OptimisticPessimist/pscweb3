# フロントエンド実装タスク (Phase 8)

Discord認証の修正が完了し、ユーザーはログインしてダッシュボード（プロジェクト一覧）まで到達できるようになりました。
本フェーズでは、各プロジェクト内部の機能（脚本、香盤表、スケジュール、メンバー管理）のUIを実装していきます。

## 1. プロジェクトレイアウトの実装
- [x] **AppLayout コンポーネント**
  - [x] サイドバーナビゲーション (Home, Script, Chart, Cast, Schedule, Settings)

## 2. 脚本管理 (Script Management)
- [x] **APIクライアント実装** (scriptsApi) <!-- id: 5 -->
- [x] **脚本一覧ページ** (ScriptList)
  - [x] アップロードボタン
  - [x] 一覧表示 (タイトル, アップロード日時)
- [x] **脚本詳細ページ** (ScriptDetail)
  - [x] PDFビューワ (ダウンロードリンク)
  - [x] キャラクター/シーン抽出結果の表示
  - [x] 統計情報の表示改善 (Acts数追加, 横並びレイアウト)
  - [x] 脚本削除機能
- [x] **デバッグ・修正**
  - [x] PDFダウンロード認証
  - [x] アップロード処理 (Content-Type/Boundary)
  - [x] Fountainパース (シーン認識/JP形式対応)
- [ ] **リファクタリング: 1プロジェクト1脚本制**
  - [x] Backend: Upload APIの更新（既存更新・香盤表自動生成・PDF生成通知・重複自動削除）
  - [x] Frontend: 脚本一覧の廃止・詳細ページへの統合
  - [x] Frontend: 香盤表ページの脚本選択削除
  - [x] Frontend: 再アップロード時のタイトル保持機能 & リビジョン管理表示

## 3. 香盤表 (Scene Chart)
- [x] **香盤表ビュー**
  - [x] シーン×キャラクターのマトリックス表示
  - [x] 出演/未出演の可視化
  - [x] 幕 (Act) の表示
- [x] **生成・設定**
  - [x] 自動生成（アップロード時）
  - [x] 手動生成ボタンの削除
  - [x] 脚本選択機能（日時表示改善済）

## 4. キャスティング (Casting)
- [x] **Backend Implementation**
  - [x] `src/api/characters.py` 作成 (Router definition)
  - [x] `GET /projects/{id}/characters` (一覧・配役取得)
  - [x] `POST /projects/{id}/characters/{char_id}/cast` (配役追加)
  - [x] `DELETE /projects/{id}/characters/{char_id}/cast` (配役解除)
  - [x] `src/main.py` にルーター登録
  - [x] Test Data: `scripts/add_dummy_member.py` 作成・実行
- [x] **Frontend Implementation**
  - [x] API Client (`charactersApi.ts`) 作成
  - [x] `CastingPage` コンポーネント実装
  - [x] キャスト一覧表示 (キャラクター vs 配役)
  - [x] 配役編集モーダル (メンバー選択)
  - [x] 権限管理UI (Viewerは編集不可)
  - [x] UI調整: ラベル変更 (Cast Name -> Memo)

## 5. 稽古スケジュール (Rehearsal Schedule) & スタッフ管理
- [x] **Backend Implementation**
  - [x] DB Migration: `default_staff_role` to ProjectMember, `staff_role` to RehearsalParticipant
  - [x] API: Update ProjectMember schemas & endpoints
  - [x] API: Update RehearsalParticipant schemas & endpoints (Adding Update/Delete)
  - [x] **Backend: Rehearsal Cast Management**
    - [x] API: Add generic Cast add/delete endpoints for Rehearsal
- [x] **Frontend Implementation**
  - [x] **メンバー設定 (Settings)**
    - [x] 基本役割 (Default Role) 編集UI
  - [x] **稽古スケジュール (Schedule)**
    - [x] カレンダービュー (Calendar)
      - [x] FullCalendar導入
      - [x] 稽古イベント表示
    - [x] 稽古詳細・作成 (Event Detail)
      - [x] 新規作成モーダル (日時, 場所, 対象シーン)
      - [x] 参加者管理・役割 (Staff Role) 編集UI
    - [x] 稽古キャスト管理 (Rehearsal Cast)
      - [x] 香盤のキャラクター一覧表示
      - [x] その稽古での配役指定 (Add/Remove Cast)

## 6. プロジェクト設定・メンバー管理
- [x] **メンバー一覧**
  - [x] メンバーリストと権限表示
  - [x] 権限変更・削除 (管理者のみ)
- [x] **招待機能**
  - [x] 招待リンクの生成とコピー機能
  - [x] 招待受諾ページ

## 7. スタッフ管理セクション (Staff Section)
- [ ] **サイドバー更新**
  - [x] CastとScheduleの間にStaffを追加
- [x] **スタッフ一覧ページ (StaffPage)**
  - [x] プロジェクトメンバー一覧表示
  - [x] スタッフ役割(Default Staff Role)の表示
  - [x] 連絡先(Discord)の表示

## Completed Debugging
- [x] **Debug**: Project Creation Failure (404/401)
    - [x] Identify cause of 404 on callback (Fixed: API Prefix mismatch)
    - [x] Identify cause of 401 on projects (Fixed: Trailing slash redirect stripping headers)
    - [x] Verify UUID handling in JWT (Confirmed working)
    - [x] Confirm Project Creation success (DB Inserted)
