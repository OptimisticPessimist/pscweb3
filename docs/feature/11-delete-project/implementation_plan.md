
# Delete Project Feature

## Goal
Allow project owners to delete their projects. This is a destructive action and requires confirmation.

## User Review Required
- **Destructive Action**: Deleting a project will remove all associated data (Members, Rehearsals, etc. via cascade if configured, or need manual cleanup).
  - *Assumption*: SQLAlchemy `cascade="all, delete-orphan"` is set on relationships in `TheaterProject`. Need to verify `models.py`.
- **UI**: A trash icon will be added to the project card. Clicking it will show a confirmation dialog.

## Proposed Changes

### Backend
#### [MODIFY] [projects.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/projects.py)
- [x] Add `@router.delete("/{project_id}")`
- [x] Check if `current_member` is "owner".
- [x] Delete `TheaterProject`.
- [x] Add `AuditLog`.

#### [CHECK] [models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- [x] Verify `TheaterProject` relationships have `cascade` set to ensure clean deletion.

### Frontend
#### [MODIFY] [dashboard.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/dashboard/api/dashboard.ts)
- [x] Add `deleteProject: (id: string) => Promise<void>`

#### [MODIFY] [DashboardPage.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/dashboard/DashboardPage.tsx)
- Add a "Delete" button (TrashIcon) to the Project Card.
- Prevent navigation when clicking delete.
- Add a "Delete Confirmation" State/Modal.

## Verification Plan
### Manual Verification
1. Create a temporary project.
2. Click the delete icon.
3. Confirm deletion in the modal.
4. Verify project disappears from the list.
5. Verify database (via checking logs or re-query) confirming it's gone.
