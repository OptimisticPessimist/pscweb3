# UI Improvements & Favicon

- [ ] Referral Name Priority
    - [ ] Backend: Update `get_project_members_public` in `api/reservations.py` to prefer `ProjectMember.display_name`.
    - [ ] Backend: Update `get_reservations` (admin) in `api/reservations.py` to join `ProjectMember` and use its display name.
    - [ ] Backend: Update CSV export to use correct display name.
- [ ] Frontend Date Formatting
    - [ ] Frontend: Standardize date display in `MilestoneSettings.tsx` (use `date-fns` `yyyy/MM/dd HH:mm`).
    - [ ] Frontend: Check and update `ReservationPage.tsx` (public form) if needed.
- [ ] Favicon
    - [ ] Generate new favicon image (Theater/Ticket theme).
    - [ ] Replace `frontend/public/favicon.ico`.
