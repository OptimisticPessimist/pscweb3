# Implementation Plan - Role-based Instruction Manual

## Goal Description
Create a role-based instruction manual in Japanese, targeted at high school students, to explain how to use the Theater Project Management System.

## User Review Required
- **Tone and Language**: Verify if the language is simple enough for high school students (avoiding jargon where possible).
- **Role Accuracy**: Confirm if "Owner", "Editor", "Viewer" covers all intended use cases.

## Proposed Changes

### `docs/`
#### [NEW] [role_manual.md](file:///f:/src/PythonProject/pscweb3-1/docs/role_manual.md)
- **Introduction**: Briefly explain the system.
- **Role Definitions**:
    - **Owner (管理者)**: Project leader, everything allowed.
    - **Editor (編集者)**: Staff, script/schedule editing.
    - **Viewer (閲覧者)**: Cast/Staff, checking info and attendance.
- **Manual by Role**:
    - **For Viewers**: How to check schedule, script, answer attendance.
    - **For Editors**: How to edit script, manage schedule, send notifications.
    - **For Owners**: How to create project, invite members, manage settings.

### `docs/feature/13-role-manual/`
- `task.md` (Copy of this task list)
- `implementation_plan.md` (This file)

## Verification Plan

### Manual Verification
1.  **Readability Check**: Read through the generated markdown to ensure it flows well.
2.  **Role Check**: Verify against `models.py` logic to ensure no feature is promised that doesn't exist.
