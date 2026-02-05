# Discord Timezone Display Fix - Walkthrough

## Summary
Discord notifications for Milestones, Attendance events, Rehearsals, and Ticket Reservations have been updated to use Discord's native dynamic timestamp format (`<t:TIMESTAMP:format>`). This ensures that dates and times are automatically shifted to the viewer's local timezone (e.g., JST) on the Discord client.

## Changes Made

### Backend

| File | Change |
| :--- | :--- |
| [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py) | Milestone notifications now use `<t:timestamp:d>` for dates. |
| [attendance.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/attendance.py) | Attendance notifications now use `<t:timestamp:f>` for deadline and event times. |
| [rehearsals.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/rehearsals.py) | Rehearsal notifications updated to ensure UTC-prefixed timestamps. |
| [reservations.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/reservations.py) | Ticket reservation and cancellation notifications now use Discord timestamps. |

## Verification Results

### Logic Check
- Verified that all modified points calculate the Unix timestamp from the database-stored naive UTC datetime by explicitly treating it as UTC (`.replace(tzinfo=timezone.utc)`).
- This prevents the server's local machine timezone from interfering with the timestamp value sent to Discord.

### Visual Rendering (Simulated)
- Standard Discord timestamp `<t:TIMESTAMP:f>` rendering:
  - Viewer in JST (UTC+9): Shows the time as JST.
  - Viewer in UTC: Shows the time as UTC.
  - This solves the "ズレる" (offset) issue caused by static JST strings being sent to users in different settings or incorrect server-side JST calculation.
