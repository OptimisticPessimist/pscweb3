# Walkthrough - User Schedule Usage

## Changes
### Backend
- **New Model**: `Milestone` (table: `milestones`)
    - Tracks important project dates (Performances, etc.)
    - Linked to `TheaterProject`
- **New Endpoints**:
    - `GET /projects/{id}/milestones`: List milestones
    - `POST /projects/{id}/milestones`: Create milestone
    - `DELETE /projects/{id}/milestones/{milestone_id}`: Delete milestone
    - `GET /users/me/schedule`: Aggregated schedule of Rehearsals and Milestones
- **Logic**: 
    - `get_my_schedule` joins `Rehearsal` (via Participant/Cast) and `Milestone` (via Project Member) and sorts by date.

### Frontend
- **New Page**: `MySchedulePage` (`/my-schedule`)
    - Displays chronological list of Rehearsals and Milestones.
    - Rehearsals show time, scene, location.
    - Milestones show colored badge.
- **Navigation**: Added "My Schedule" to Sidebar.

## Verification Results
### Automated Verification
Ran `backend/verify_schedule.py` which:
1. Created test users and projects.
2. Created rehearsals with participants.
3. Created milestones.
4. Verified that `get_my_schedule` logic correctly aggregates and sorts them.
5. **Result**: PASSED.

### Manual Verification Steps
1. Login to the application.
2. Navigate to "My Schedule" from the sidebar.
3. Verify that upcoming rehearsals for your projects are listed.
4. (Optional) Use API or future UI to create a Milestone and verify it appears.
