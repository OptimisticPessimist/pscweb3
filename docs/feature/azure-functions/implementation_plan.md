# Implement Milestone Settings UI

## Goal Description
Provide a user interface for managing project milestones (create, list, delete) within the Project Settings page.

## Proposed Changes

### Frontend
#### [MODIFY] [projects.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/api/projects.ts)
- Add API methods: `getMilestones`, `createMilestone`, `deleteMilestone`.

#### [NEW] [MilestoneSettings.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/components/MilestoneSettings.tsx)
- Create a new component to list existing milestones and provide a form to add new ones.
- Features:
    - List view with delete button
    - Add form (Title, Date, optional EndDate, Color, Location, Description)

#### [MODIFY] [ProjectSettingsPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/pages/ProjectSettingsPage.tsx)
- Integrate `MilestoneSettings` component below the General Settings or Members section.
