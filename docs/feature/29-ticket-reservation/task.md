# Milestone Capacity Management

- [x] Backend: Update Milestone Schemas and Query
    - [x] Create `MilestoneUpdate` schema in `schemas/project.py`.
    - [x] Update `MilestoneResponse` to include `current_reservation_count`.
    - [x] Update `list_milestones` in `api/projects.py` to calculate `current_reservation_count` (sum of reserved tickets).
- [x] Backend: Add Update Endpoint
    - [x] Add `PATCH /projects/{project_id}/milestones/{milestone_id}` in `api/projects.py` to allow updating capacity (and other fields).
- [x] Frontend: Update API Client and Types
    - [x] Update `projectsApi` in `frontend/src/features/projects/api/projects.ts` (implied path) to include `updateMilestone`.
    - [x] Update `Milestone` type in `frontend/src/types/index.ts` (or wherever it is) to include `current_reservation_count`.
- [x] Frontend: UI Updates
    - [x] Modify `MilestoneSettings.tsx` to display "Current / Max".
    - [x] Implement inline editing or a small form to update `reservation_capacity`.
- [x] Frontend: Reservation List Link
    - [x] Add link to `/projects/{projectId}/reservations?milestoneId={milestone.id}` in `MilestoneSettings.tsx`.
