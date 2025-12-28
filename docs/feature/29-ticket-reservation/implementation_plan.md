# UI Improvements & Favicon Update

## 目標
1.  **日付表示の統一**: フロントエンド（特にマイルストーン設定）での日時表示を `yyyy/MM/dd HH:mm` 等の統一された形式にする。
2.  **紹介者名の優先順位変更**: 予約時の紹介者選択リストおよび予約一覧・CSVにおける紹介者名を、「プロジェクトメンバーの表示名 (`ProjectMember.display_name`)」 > 「ユーザー表示名 (`User.screen_name`)」 > 「Discord名」の優先順位で表示する。
3.  **Favicon変更**: アプリケーションのファビコンを更新する。

## 変更内容

### Backend
#### [MODIFY] [reservations.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/reservations.py)
- `get_project_members_public`: `User` と `ProjectMember` を結合して取得し、`display_name` を優先して返却する。
- `get_reservations`: 予約一覧取得時、`ProjectMember` を外部結合（Outer Join）し、プロジェクト内での表示名を取得・返却する。
- `export_reservations`: CSV出力時も同様にプロジェクト内表示名を使用する。

### Frontend
#### [MODIFY] [MilestoneSettings.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/components/MilestoneSettings.tsx)
- `toLocaleString()` での表示をやめ、`date-fns` の `format` 関数を使用して `yyyy/MM/dd HH:mm` 形式に統一する。

#### [NEW] [favicon.svg / favicon.ico](file:///f:/src/PythonProject/pscweb3-1/frontend/public/favicon.ico)
- 新しいファビコン画像を生成・配置する。

## 検証計画
1.  **紹介者名表示**:
    - プロジェクトメンバーの「表示名」を設定したユーザーを用意する。
    - 予約フォームの紹介者リストにその「表示名」が表示されるか確認。
    - 予約後の管理画面一覧およびCSVで「表示名」が表示されるか確認。
2.  **日付表示**:
    - マイルストーン設定画面で、日時が意図したフォーマット (`yyyy/MM/dd HH:mm`) で表示されているか確認。
3.  **Favicon**:
    - ブラウザのタブに新しいアイコンが表示されるか確認。
