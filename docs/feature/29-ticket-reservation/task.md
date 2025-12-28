# Reservation Cancellation, Discord Notifications, and Public Schedule

- [x] Backend: Update API
    - [x] `reservations.py`: Add `POST /public/reservations/cancel` endpoint for cancellation verifying email.
    - [x] `reservations.py`: Add `GET /api/public/schedule` to retrieve future milestones from public projects.
    - [x] `reservations.py`: Integrate `DiscordService` to send notifications on create and cancel.
    - [x] `email.py`: Add `reservation_id` to confirmation email.
- [x] Frontend: New Pages
    - [x] Create `PublicSchedulePage.tsx`: Display list of future milestones with "Reserve" buttons.
    - [x] Create `ReservationCancelPage.tsx`: Form to input Reservation ID and Email to cancel.
- [x] Frontend: Update Existing Pages
    - [x] `App.tsx`: Add routes for `/schedule` (public) and `/reservations/cancel`.
    - [x] `ReservationCompletedPage.tsx`: Display Reservation ID prominently and link to cancel page.
    - [x] API client: Add `cancelReservation` and `getPublicSchedule` methods.
- [x] Verification
    - [x] Add tests for cancellation flow and public schedule.
    - [x] Mock Discord notifications in tests.
