# マイルストーンの時間管理と予約情報の強化

- [ ] マイルストーンの時間指定サポート
    - [ ] Frontend: `MilestoneSettings.tsx` を更新し、開始・終了日時を `datetime-local` で扱えるようにする。
    - [ ] Backend: `schemas/project.py` が日時情報を正しく処理できるか確認する。
- [ ] 予約連絡へのプロジェクト名追加
    - [ ] Backend: `email_service.send_reservation_confirmation` を更新し、`project_name` を受け取れるようにする。
    - [ ] Backend: `api/reservations.py` でプロジェクト名を取得し、メールサービスに渡す。
    - [ ] Frontend: `ReservationCompletedPage.tsx` のGoogleカレンダーリンクにプロジェクト名を含める。
