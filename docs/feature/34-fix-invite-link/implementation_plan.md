# Implementation Plan - Fix Invite Link Generation

The invite link generation fails because the frontend API client appends an extra `/invitations` prefix to the API paths, resulting in 404 errors.

## Problem
The frontend API client is configured with `baseURL: '/api'`.
The backend routes are:
- `POST /api/projects/{project_id}/invitations`
- `GET /api/invitations/{token}`
- `POST /api/invitations/{token}/accept`

The frontend code in `invitations.ts` calls:
- `POST /invitations/projects/{projectId}/invitations` -> `/api/invitations/projects/...` (Incorrect)
- `GET /invitations/invitations/{token}` -> `/api/invitations/invitations/...` (Incorrect)

## Proposed Changes

### Frontend

#### [MODIFY] [invitations.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/features/projects/api/invitations.ts)
- Remove the leading `/invitations` from all API paths.

```typescript
// Before
async createInvitation(projectId: string, data: InvitationCreate): Promise<InvitationResponse> {
    const response = await apiClient.post(`/invitations/projects/${projectId}/invitations`, data);
    return response.data;
},
// After
async createInvitation(projectId: string, data: InvitationCreate): Promise<InvitationResponse> {
    const response = await apiClient.post(`/projects/${projectId}/invitations`, data);
    return response.data;
},
```

Same for `getInvitation` and `acceptInvitation`.

## Verification Plan

### Automated Tests
- Run existing backend tests to ensure the backend routes are working as expected.
  - `pytest backend/tests/integration/test_api_invitations.py` (if exists)
- If no specific invitation tests exist, I will create a reproduction script `backend/tests/repro_issue_invite.py` to verify the backend routes against the expected URLs.

### Manual Verification
- Since I cannot run the frontend in a browser, I will verify the fix by code inspection and by ensuring the paths match the backend routes exactly.
