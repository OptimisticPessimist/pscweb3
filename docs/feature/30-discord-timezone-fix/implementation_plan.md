# Discord Timezone Display Fix

## Goal
Ensure Discord notifications for Milestones and Attendance display dates and times in the user's local timezone (JST) by utilizing Discord's native timestamp formatting.

## User Review Required
> [!IMPORTANT]
> This change replaces hardcoded date strings (e.g., "2024/01/01") with Discord timestamp codes (e.g., `<t:1704067200:d>`). This ensures the date/time is rendered in the viewer's local time setting on Discord.

## Proposed Changes

### Backend

#### [MODIFY] [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
- In `create_milestone` and `delete_milestone` (if applicable), change string formatting of `start_date` and `end_date` to use Discord timestamp format.
- Format: `<t:TIMESTAMP:f>` (Short Date Time) or `<t:TIMESTAMP:d>` (Short Date) depending on whether time is relevant. Milestones usually just have dates, but the DB field is DateTime. If time is 00:00, maybe just Date?
    - `Milestone` model has `start_date` as DateTime.
    - If it's a "day" event, we might prefer Date format.
    - Proposal: Use `<t:TIMESTAMP:f>` for full clarity or `<t:TIMESTAMP:d>` if it's strictly a date. The current implementation uses `%Y/%m/%d`, implying date only. I will use `<t:TIMESTAMP:d>` for Milestones.

#### [MODIFY] [attendance.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/attendance.py)
- In `create_attendance_event`, change `deadline` and `schedule_date` formatting to Discord timestamp format.
- Format: `<t:TIMESTAMP:f>` (Short Date Time) since these have specific times.

## Verification Plan

### Automated Tests
- Create or update a test case that triggers these notifications and verify the payload content contains `<t:` patterns instead of raw date strings.
- Since we can't easily verify the "visual" rendering in Discord without a real client, checking the payload format is sufficient.

### Manual Verification
- N/A (We rely on unit/integration tests for the payload format).
